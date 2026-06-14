"""Metric calculations.

Pure functions that turn the collected stories/PRs into the productivity,
AI-usage and rework metric objects. No I/O, fully unit-testable.
"""

from __future__ import annotations

from statistics import mean

from ai_engineering_metrics.config import PricingConfig
from ai_engineering_metrics.domain.models import (
    AIUsageMetrics,
    Deployment,
    DoraMetrics,
    ProductivityMetrics,
    PullRequest,
    ReworkMetrics,
    Story,
)


def _safe_div(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return round(numerator / denominator, 4)


def compute_productivity(stories: list[Story]) -> ProductivityMetrics:
    if not stories:
        return ProductivityMetrics()

    without_ai = sum(s.estimate_without_ai_hours for s in stories)
    with_ai = sum(s.estimate_with_ai_hours for s in stories)
    saved = without_ai - with_ai

    story_lead_times = [s.lead_time_hours for s in stories if s.lead_time_hours is not None]
    pr_lead_times = [
        pr.time_to_merge_hours
        for s in stories
        for pr in s.pull_requests
        if pr.time_to_merge_hours is not None
    ]
    total_prs = sum(len(s.pull_requests) for s in stories)

    return ProductivityMetrics(
        estimated_hours_without_ai=round(without_ai, 2),
        estimated_hours_with_ai=round(with_ai, 2),
        hours_saved=round(saved, 2),
        savings_percent=round(_safe_div(saved, without_ai) * 100, 2),
        avg_lead_time_hours=round(mean(story_lead_times), 2) if story_lead_times else None,
        avg_pr_lead_time_hours=round(mean(pr_lead_times), 2) if pr_lead_times else None,
        prs_per_story=round(_safe_div(total_prs, len(stories)), 2),
    )


def compute_ai_usage(
    stories: list[Story],
    pricing: PricingConfig,
    *,
    extra_pull_requests: list[PullRequest] | None = None,
) -> AIUsageMetrics:
    if not stories:
        return AIUsageMetrics()

    extra = extra_pull_requests or []
    total_tokens = sum(s.ai_tokens for s in stories)
    total_prs = sum(len(s.pull_requests) for s in stories) + len(extra)
    total_added = sum(s.total_additions for s in stories) + sum(pr.additions for pr in extra)
    total_changed = sum(s.total_changed_lines for s in stories) + sum(
        pr.total_changed_lines for pr in extra
    )
    total_points = sum(s.story_points or 0 for s in stories)
    hours_saved = sum(s.hours_saved for s in stories)

    estimated_cost = round(total_tokens / 1_000_000 * pricing.default_per_1m, 2)

    return AIUsageMetrics(
        total_tokens=total_tokens,
        tokens_per_story=_safe_div(total_tokens, len(stories)),
        tokens_per_pr=_safe_div(total_tokens, total_prs),
        tokens_per_added_line=_safe_div(total_tokens, total_added),
        tokens_per_changed_line=_safe_div(total_tokens, total_changed),
        tokens_per_story_point=_safe_div(total_tokens, total_points),
        tokens_per_hour_saved=_safe_div(total_tokens, hours_saved),
        estimated_cost=estimated_cost,
        cost_per_story=round(_safe_div(estimated_cost, len(stories)), 2),
        cost_per_pr=round(_safe_div(estimated_cost, total_prs), 2),
        cost_per_hour_saved=round(_safe_div(estimated_cost, hours_saved), 2),
    )


def compute_rework(
    stories: list[Story],
    *,
    extra_pull_requests: list[PullRequest] | None = None,
) -> ReworkMetrics:
    prs = [pr for s in stories for pr in s.pull_requests]
    prs.extend(extra_pull_requests or [])
    if not prs:
        return ReworkMetrics()

    merge_times = [pr.time_to_merge_hours for pr in prs if pr.time_to_merge_hours is not None]

    return ReworkMetrics(
        avg_time_to_merge_hours=round(mean(merge_times), 2) if merge_times else None,
        total_review_cycles=sum(pr.review_cycles for pr in prs),
        total_review_comments=sum(pr.review_comments for pr in prs),
        total_requested_changes=sum(pr.requested_changes for pr in prs),
        total_commits_after_review=sum(pr.commits_after_review for pr in prs),
        reverts_detected=sum(pr.reverts_detected for pr in prs),
        files_touched_again_later=_files_touched_again(stories),
    )


def _dora_deploy_freq_label(freq_per_day: float) -> str:
    if freq_per_day >= 1.0:
        return "elite"
    if freq_per_day >= 1 / 7:
        return "high"
    if freq_per_day >= 1 / 30:
        return "medium"
    return "low"


def _dora_lead_time_label(hours: float) -> str:
    if hours < 1:
        return "elite"
    if hours < 168:
        return "high"
    if hours < 720:
        return "medium"
    return "low"


def _dora_cfr_label(cfr: float) -> str:
    if cfr <= 15:
        return "elite"
    if cfr <= 30:
        return "high"
    if cfr <= 45:
        return "medium"
    return "low"


def _dora_mttr_label(hours: float) -> str:
    if hours < 1:
        return "elite"
    if hours < 24:
        return "high"
    if hours < 168:
        return "medium"
    return "low"


def compute_dora(deployments: list[Deployment], period_days: int = 30) -> DoraMetrics:
    """Compute the four DORA metrics from a list of deployment events."""
    if not deployments:
        return DoraMetrics(period_days=period_days)

    freq = len(deployments) / period_days if period_days else 0.0

    lead_times = [d.lead_time_hours for d in deployments if d.lead_time_hours is not None]
    avg_lead_time = round(mean(lead_times), 2) if lead_times else None

    failures = [d for d in deployments if d.is_failure]
    cfr = round(len(failures) / len(deployments) * 100, 2)

    mttr_values = [d.mttr_hours for d in deployments if d.mttr_hours is not None]
    avg_mttr = round(mean(mttr_values), 2) if mttr_values else None

    return DoraMetrics(
        deployment_frequency=round(freq, 4),
        deployment_frequency_label=_dora_deploy_freq_label(freq),
        lead_time_hours=avg_lead_time,
        lead_time_label=_dora_lead_time_label(avg_lead_time)
        if avg_lead_time is not None
        else "unknown",
        change_failure_rate=cfr,
        change_failure_rate_label=_dora_cfr_label(cfr),
        mttr_hours=avg_mttr,
        mttr_label=_dora_mttr_label(avg_mttr) if avg_mttr is not None else "unknown",
        deployments=deployments,
        period_days=period_days,
    )


def _files_touched_again(stories: list[Story]) -> int:
    """Heuristic for churn: PRs that modify many files are more likely to be
    revisited. Without per-file diffs we approximate with PRs that report
    commits-after-review, which is the strongest available rework signal.
    """
    return sum(1 for s in stories for pr in s.pull_requests if pr.commits_after_review > 0)
