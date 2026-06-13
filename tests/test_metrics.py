from datetime import UTC, datetime

from ai_engineering_metrics.config import PricingConfig
from ai_engineering_metrics.domain import metrics
from ai_engineering_metrics.domain.models import PullRequest, Story

UTC = UTC


def _story(**kwargs) -> Story:
    base = dict(
        key="X-1",
        summary="s",
        status="Done",
        ai_tokens=100_000,
        estimate_without_ai_hours=40,
        estimate_with_ai_hours=20,
        story_points=8,
    )
    base.update(kwargs)
    return Story(**base)


def _pr(**kwargs) -> PullRequest:
    base = dict(
        number=1,
        title="t",
        author="dev",
        repository="org/repo",
        branch="b",
        status="merged",
        additions=200,
        deletions=50,
    )
    base.update(kwargs)
    return PullRequest(**base)


def test_productivity_savings():
    stories = [_story(), _story(key="X-2", estimate_without_ai_hours=60, estimate_with_ai_hours=30)]
    p = metrics.compute_productivity(stories)
    assert p.estimated_hours_without_ai == 100
    assert p.estimated_hours_with_ai == 50
    assert p.hours_saved == 50
    assert p.savings_percent == 50.0


def test_productivity_lead_time_and_prs_per_story():
    story = _story(
        created_at=datetime(2026, 5, 1, tzinfo=UTC),
        resolved_at=datetime(2026, 5, 2, tzinfo=UTC),
        pull_requests=[_pr(), _pr(number=2)],
    )
    p = metrics.compute_productivity([story])
    assert p.avg_lead_time_hours == 24.0
    assert p.prs_per_story == 2.0


def test_ai_usage_ratios_and_cost():
    story = _story(ai_tokens=300_000, pull_requests=[_pr(additions=200, deletions=100)])
    usage = metrics.compute_ai_usage([story], PricingConfig(default_per_1m=6.0))
    assert usage.total_tokens == 300_000
    assert usage.tokens_per_added_line == 1500.0  # 300k / 200
    assert usage.tokens_per_changed_line == 1000.0  # 300k / 300
    assert usage.tokens_per_story_point == 37500.0  # 300k / 8
    assert usage.estimated_cost == 1.8  # 0.3M * 6


def test_ai_usage_handles_zero_division():
    story = _story(
        ai_tokens=0, estimate_without_ai_hours=0, estimate_with_ai_hours=0, story_points=None
    )
    usage = metrics.compute_ai_usage([story], PricingConfig())
    assert usage.tokens_per_hour_saved == 0.0
    assert usage.cost_per_hour_saved == 0.0


def test_rework_aggregates_review_signals():
    story = _story(
        pull_requests=[
            _pr(review_cycles=3, requested_changes=2, review_comments=10, commits_after_review=4),
            _pr(
                number=2,
                review_cycles=1,
                requested_changes=0,
                review_comments=2,
                reverts_detected=1,
            ),
        ]
    )
    r = metrics.compute_rework([story])
    assert r.total_review_cycles == 4
    assert r.total_requested_changes == 2
    assert r.total_review_comments == 12
    assert r.reverts_detected == 1
    assert r.files_touched_again_later == 1  # only the PR with commits_after_review > 0


def test_empty_inputs_are_safe():
    assert metrics.compute_productivity([]).hours_saved == 0.0
    assert metrics.compute_ai_usage([], PricingConfig()).total_tokens == 0
    assert metrics.compute_rework([]).total_review_cycles == 0
