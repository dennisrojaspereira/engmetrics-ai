"""AI Dependency Risk Score (0-100).

A higher score means the delivery leans heavily on AI while showing weak signals
of healthy, low-rework, well-tested output. Every component is normalised to
0..1 (1 = worst) and combined with explicit, tunable weights so the breakdown is
fully explainable in the dashboard.
"""

from __future__ import annotations

from ai_engineering_metrics.domain.models import (
    AIUsageMetrics,
    PullRequest,
    PullRequestRisk,
    QualityMetrics,
    ReworkMetrics,
    RiskComponent,
    RiskScore,
    Story,
    StoryRisk,
)

# Reference points where a signal is considered "fully bad" (normalized -> 1.0).
TOKENS_PER_HOUR_SAVED_CAP = 200_000  # very token-hungry per hour saved
TOKENS_PER_CHANGED_LINE_CAP = 1_500
LOW_SAVINGS_FLOOR = 40.0  # below this % savings starts counting as risk
REVIEW_CYCLES_CAP = 6
REQUESTED_CHANGES_CAP = 8
COMPLEXITY_CAP = 25.0  # cyclomatic complexity considered high
COVERAGE_TARGET = 80.0

EPIC_WEIGHTS = {
    "ai_intensity": 0.20,
    "low_savings": 0.18,
    "low_coverage": 0.15,
    "high_complexity": 0.12,
    "review_churn": 0.13,
    "requested_changes": 0.10,
    "vulnerabilities": 0.07,
    "static_bugs": 0.05,
}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _level(score: float) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "moderate"
    return "low"


def _build(components: dict[str, tuple[float, float]]) -> RiskScore:
    """components: name -> (weight, normalized 0..1)."""
    parts: list[RiskComponent] = []
    total = 0.0
    for name, (weight, normalized) in components.items():
        normalized = _clamp(normalized)
        contribution = round(weight * normalized * 100, 2)
        total += contribution
        parts.append(
            RiskComponent(
                name=name, weight=weight, normalized=round(normalized, 3), contribution=contribution
            )
        )
    score = round(total, 1)
    return RiskScore(score=score, level=_level(score), components=parts)


def compute_epic_risk(
    stories: list[Story],
    ai_usage: AIUsageMetrics,
    quality: QualityMetrics,
    rework: ReworkMetrics,
) -> RiskScore:
    story_count = max(len(stories), 1)

    ai_intensity = (
        ai_usage.tokens_per_hour_saved / TOKENS_PER_HOUR_SAVED_CAP
        if ai_usage.tokens_per_hour_saved
        else 0.0
    )

    savings_pct = 0.0
    without = sum(s.estimate_without_ai_hours for s in stories)
    saved = sum(s.hours_saved for s in stories)
    if without:
        savings_pct = saved / without * 100
    low_savings = (LOW_SAVINGS_FLOOR - savings_pct) / LOW_SAVINGS_FLOOR

    coverage = quality.test_coverage_percent
    low_coverage = (COVERAGE_TARGET - coverage) / COVERAGE_TARGET if coverage is not None else 0.5

    complexity = quality.cyclomatic_complexity
    high_complexity = complexity / COMPLEXITY_CAP if complexity is not None else 0.0

    review_churn = rework.total_review_cycles / (REVIEW_CYCLES_CAP * story_count)
    requested = rework.total_requested_changes / (REQUESTED_CHANGES_CAP * story_count)

    vulns = quality.vulnerabilities or 0
    vulnerabilities = vulns / 5.0  # 5+ vulns => fully bad
    bugs = quality.static_bugs or 0
    static_bugs = bugs / 10.0  # 10+ bugs => fully bad

    return _build(
        {
            "ai_intensity": (EPIC_WEIGHTS["ai_intensity"], ai_intensity),
            "low_savings": (EPIC_WEIGHTS["low_savings"], low_savings),
            "low_coverage": (EPIC_WEIGHTS["low_coverage"], low_coverage),
            "high_complexity": (EPIC_WEIGHTS["high_complexity"], high_complexity),
            "review_churn": (EPIC_WEIGHTS["review_churn"], review_churn),
            "requested_changes": (EPIC_WEIGHTS["requested_changes"], requested),
            "vulnerabilities": (EPIC_WEIGHTS["vulnerabilities"], vulnerabilities),
            "static_bugs": (EPIC_WEIGHTS["static_bugs"], static_bugs),
        }
    )


def compute_story_risk(story: Story, quality: QualityMetrics) -> StoryRisk:
    changed = story.total_changed_lines or 1
    ai_intensity = (story.ai_tokens / changed) / TOKENS_PER_CHANGED_LINE_CAP

    saved_pct = 0.0
    if story.estimate_without_ai_hours:
        saved_pct = story.hours_saved / story.estimate_without_ai_hours * 100
    low_savings = (LOW_SAVINGS_FLOOR - saved_pct) / LOW_SAVINGS_FLOOR

    cycles = sum(pr.review_cycles for pr in story.pull_requests)
    changes = sum(pr.requested_changes for pr in story.pull_requests)
    review_churn = cycles / REVIEW_CYCLES_CAP
    requested = changes / REQUESTED_CHANGES_CAP

    coverage = quality.test_coverage_percent
    low_coverage = (COVERAGE_TARGET - coverage) / COVERAGE_TARGET if coverage is not None else 0.5

    score = _build(
        {
            "ai_intensity": (0.30, ai_intensity),
            "low_savings": (0.25, low_savings),
            "review_churn": (0.20, review_churn),
            "requested_changes": (0.15, requested),
            "low_coverage": (0.10, low_coverage),
        }
    )
    return StoryRisk(key=story.key, score=score.score, level=score.level)


def compute_pr_risk(pr: PullRequest, story_tokens: int, quality: QualityMetrics) -> PullRequestRisk:
    changed = pr.total_changed_lines or 1
    ai_intensity = (story_tokens / changed) / TOKENS_PER_CHANGED_LINE_CAP
    review_churn = pr.review_cycles / REVIEW_CYCLES_CAP
    requested = pr.requested_changes / REQUESTED_CHANGES_CAP
    after_review = min(pr.commits_after_review / 5.0, 1.0)
    reverts = min(pr.reverts_detected / 1.0, 1.0)

    coverage = quality.test_coverage_percent
    low_coverage = (COVERAGE_TARGET - coverage) / COVERAGE_TARGET if coverage is not None else 0.5

    score = _build(
        {
            "ai_intensity": (0.25, ai_intensity),
            "review_churn": (0.22, review_churn),
            "requested_changes": (0.18, requested),
            "commits_after_review": (0.15, after_review),
            "reverts": (0.10, reverts),
            "low_coverage": (0.10, low_coverage),
        }
    )
    return PullRequestRisk(
        number=pr.number,
        repository=pr.repository,
        title=pr.title,
        score=score.score,
        level=score.level,
        components=score.components,
    )
