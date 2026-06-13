from ai_engineering_metrics.domain import risk
from ai_engineering_metrics.domain.models import (
    AIUsageMetrics,
    PullRequest,
    QualityMetrics,
    ReworkMetrics,
    Story,
)


def _story(**kwargs) -> Story:
    base = dict(
        key="X-1",
        summary="s",
        status="Done",
        ai_tokens=100_000,
        estimate_without_ai_hours=40,
        estimate_with_ai_hours=20,
    )
    base.update(kwargs)
    return Story(**base)


def test_score_in_bounds_and_components_sum():
    stories = [
        _story(
            pull_requests=[
                PullRequest(
                    number=1,
                    title="t",
                    author="d",
                    repository="r",
                    branch="b",
                    status="merged",
                    additions=300,
                    deletions=100,
                    review_cycles=2,
                    requested_changes=1,
                )
            ]
        )
    ]
    usage = AIUsageMetrics(tokens_per_hour_saved=50_000)
    quality = QualityMetrics(
        test_coverage_percent=70, cyclomatic_complexity=12, vulnerabilities=1, static_bugs=3
    )
    rework = ReworkMetrics(total_review_cycles=2, total_requested_changes=1)

    score = risk.compute_epic_risk(stories, usage, quality, rework)
    assert 0 <= score.score <= 100
    assert score.level in {"low", "moderate", "high", "critical"}
    assert round(sum(c.contribution for c in score.components), 1) == score.score


def test_high_risk_profile_scores_higher_than_low():
    stories = [_story(estimate_with_ai_hours=38)]  # almost no savings
    bad_usage = AIUsageMetrics(tokens_per_hour_saved=300_000)
    bad_quality = QualityMetrics(
        test_coverage_percent=20, cyclomatic_complexity=30, vulnerabilities=6, static_bugs=12
    )
    bad_rework = ReworkMetrics(total_review_cycles=12, total_requested_changes=16)
    high = risk.compute_epic_risk(stories, bad_usage, bad_quality, bad_rework)

    good_stories = [_story(estimate_with_ai_hours=10)]  # big savings
    good_usage = AIUsageMetrics(tokens_per_hour_saved=5_000)
    good_quality = QualityMetrics(
        test_coverage_percent=92, cyclomatic_complexity=5, vulnerabilities=0, static_bugs=0
    )
    good_rework = ReworkMetrics(total_review_cycles=1, total_requested_changes=0)
    low = risk.compute_epic_risk(good_stories, good_usage, good_quality, good_rework)

    assert high.score > low.score
    assert high.level in {"high", "critical"}


def test_pr_and_story_risk_levels_are_valid():
    story = _story(
        pull_requests=[
            PullRequest(
                number=7,
                title="t",
                author="d",
                repository="r",
                branch="b",
                status="merged",
                additions=100,
                deletions=20,
                review_cycles=4,
                requested_changes=3,
                commits_after_review=5,
            )
        ]
    )
    quality = QualityMetrics(test_coverage_percent=60)
    sr = risk.compute_story_risk(story, quality)
    pr = risk.compute_pr_risk(story.pull_requests[0], story.ai_tokens, quality)
    assert 0 <= sr.score <= 100
    assert 0 <= pr.score <= 100
