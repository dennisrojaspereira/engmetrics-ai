"""Realistic fake data so the whole pipeline runs with ``--mock``.

Provides drop-in replacements for the JIRA, GitHub and quality clients. The data
models 1 epic, 5 stories and 8 pull requests with believable diff stats, review
churn and AI-token usage so every chart and metric on the dashboard is populated.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ai_engineering_metrics.domain.models import Epic, PullRequest, QualityMetrics, Story

_BASE = datetime(2026, 5, 1, 9, 0, tzinfo=UTC)

EPIC_KEY = "KAN-20001"


def _dt(day_offset: int, hour: int = 9) -> datetime:
    return _BASE + timedelta(days=day_offset, hours=hour - 9)


def _epic() -> Epic:
    return Epic(
        key=EPIC_KEY,
        summary="AI-assisted checkout revamp",
        status="In Progress",
        assignee="Ana Müller",
        labels=["ai-pilot", "checkout", "q2-2026"],
        created_at=_dt(0),
        updated_at=_dt(30),
    )


# (story fields..., [pull requests]) ----------------------------------------
def _stories() -> list[Story]:
    return [
        Story(
            key="KAN-20002",
            summary="Tokenise saved payment methods",
            status="Done",
            assignee="Ana Müller",
            labels=["backend", "ai-pilot"],
            story_points=8,
            ai_tokens=480_000,
            estimate_without_ai_hours=40,
            estimate_with_ai_hours=22,
            created_at=_dt(1),
            updated_at=_dt(9),
            resolved_at=_dt(9, 17),
            pull_requests=[
                PullRequest(
                    number=1421,
                    title="KAN-20002 Tokenise card vault",
                    author="anamuller",
                    repository="acme/payments-api",
                    branch="feature/KAN-20002-card-vault",
                    status="merged",
                    created_at=_dt(3),
                    merged_at=_dt(5, 14),
                    commits=12,
                    changed_files=18,
                    additions=940,
                    deletions=210,
                    review_comments=14,
                    requested_changes=2,
                    review_cycles=3,
                    commits_after_review=4,
                    reverts_detected=0,
                    reviewers=["liu-wei", "pedro-souza"],
                ),
                PullRequest(
                    number=1437,
                    title="KAN-20002 Vault migration follow-up",
                    author="anamuller",
                    repository="acme/payments-api",
                    branch="feature/KAN-20002-vault-migration",
                    status="merged",
                    created_at=_dt(6),
                    merged_at=_dt(7, 11),
                    commits=4,
                    changed_files=6,
                    additions=180,
                    deletions=40,
                    review_comments=3,
                    requested_changes=0,
                    review_cycles=1,
                    commits_after_review=0,
                    reverts_detected=0,
                    reviewers=["liu-wei"],
                ),
            ],
        ),
        Story(
            key="KAN-20003",
            summary="One-click checkout UI",
            status="Done",
            assignee="Liu Wei",
            labels=["frontend", "ai-pilot"],
            story_points=5,
            ai_tokens=620_000,
            estimate_without_ai_hours=32,
            estimate_with_ai_hours=14,
            created_at=_dt(2),
            updated_at=_dt(12),
            resolved_at=_dt(12, 16),
            pull_requests=[
                PullRequest(
                    number=884,
                    title="KAN-20003 One-click checkout flow",
                    author="liu-wei",
                    repository="acme/web-storefront",
                    branch="feat/KAN-20003-one-click",
                    status="merged",
                    created_at=_dt(5),
                    merged_at=_dt(9, 18),
                    commits=22,
                    changed_files=34,
                    additions=1860,
                    deletions=320,
                    review_comments=28,
                    requested_changes=4,
                    review_cycles=5,
                    commits_after_review=9,
                    reverts_detected=1,
                    reviewers=["anamuller", "sara-nilsson"],
                ),
                PullRequest(
                    number=901,
                    title="KAN-20003 Fix checkout a11y",
                    author="liu-wei",
                    repository="acme/web-storefront",
                    branch="fix/KAN-20003-a11y",
                    status="merged",
                    created_at=_dt(10),
                    merged_at=_dt(11, 13),
                    commits=3,
                    changed_files=5,
                    additions=120,
                    deletions=60,
                    review_comments=2,
                    requested_changes=0,
                    review_cycles=1,
                    commits_after_review=1,
                    reverts_detected=0,
                    reviewers=["sara-nilsson"],
                ),
            ],
        ),
        Story(
            key="KAN-20004",
            summary="Fraud scoring service integration",
            status="Done",
            assignee="Pedro Souza",
            labels=["backend", "security"],
            story_points=13,
            ai_tokens=310_000,
            estimate_without_ai_hours=56,
            estimate_with_ai_hours=44,
            created_at=_dt(3),
            updated_at=_dt(20),
            resolved_at=_dt(20, 15),
            pull_requests=[
                PullRequest(
                    number=1455,
                    title="KAN-20004 Integrate fraud scoring",
                    author="pedro-souza",
                    repository="acme/payments-api",
                    branch="feature/KAN-20004-fraud-scoring",
                    status="merged",
                    created_at=_dt(8),
                    merged_at=_dt(14, 12),
                    commits=18,
                    changed_files=24,
                    additions=1320,
                    deletions=180,
                    review_comments=21,
                    requested_changes=3,
                    review_cycles=4,
                    commits_after_review=6,
                    reverts_detected=0,
                    reviewers=["anamuller", "liu-wei"],
                ),
            ],
        ),
        Story(
            key="KAN-20005",
            summary="Checkout analytics events",
            status="In Review",
            assignee="Sara Nilsson",
            labels=["frontend", "analytics"],
            story_points=3,
            ai_tokens=150_000,
            estimate_without_ai_hours=20,
            estimate_with_ai_hours=9,
            created_at=_dt(6),
            updated_at=_dt(18),
            resolved_at=None,
            pull_requests=[
                PullRequest(
                    number=915,
                    title="KAN-20005 Emit checkout analytics",
                    author="sara-nilsson",
                    repository="acme/web-storefront",
                    branch="feat/KAN-20005-analytics",
                    status="open",
                    created_at=_dt(15),
                    merged_at=None,
                    commits=7,
                    changed_files=11,
                    additions=430,
                    deletions=70,
                    review_comments=6,
                    requested_changes=1,
                    review_cycles=2,
                    commits_after_review=2,
                    reverts_detected=0,
                    reviewers=["liu-wei"],
                ),
                PullRequest(
                    number=921,
                    title="KAN-20005 Analytics schema tweak",
                    author="sara-nilsson",
                    repository="acme/data-pipeline",
                    branch="feat/KAN-20005-schema",
                    status="open",
                    created_at=_dt(17),
                    merged_at=None,
                    commits=2,
                    changed_files=3,
                    additions=90,
                    deletions=10,
                    review_comments=1,
                    requested_changes=0,
                    review_cycles=1,
                    commits_after_review=0,
                    reverts_detected=0,
                    reviewers=[],
                ),
            ],
        ),
        Story(
            key="KAN-20006",
            summary="Localised checkout copy",
            status="Done",
            assignee="Ana Müller",
            labels=["frontend", "i18n", "ai-pilot"],
            story_points=2,
            ai_tokens=95_000,
            estimate_without_ai_hours=16,
            estimate_with_ai_hours=5,
            created_at=_dt(10),
            updated_at=_dt(16),
            resolved_at=_dt(16, 14),
            pull_requests=[
                PullRequest(
                    number=948,
                    title="KAN-20006 Localise checkout strings",
                    author="anamuller",
                    repository="acme/web-storefront",
                    branch="feat/KAN-20006-i18n",
                    status="merged",
                    created_at=_dt(13),
                    merged_at=_dt(15, 10),
                    commits=5,
                    changed_files=9,
                    additions=260,
                    deletions=30,
                    review_comments=4,
                    requested_changes=0,
                    review_cycles=1,
                    commits_after_review=1,
                    reverts_detected=0,
                    reviewers=["sara-nilsson"],
                ),
            ],
        ),
    ]


def _quality() -> QualityMetrics:
    return QualityMetrics(
        cyclomatic_complexity=14.2,
        cognitive_complexity=19.6,
        duplication_percent=4.8,
        code_smells=37,
        static_bugs=6,
        vulnerabilities=2,
        test_coverage_percent=71.5,
        source="mock",
    )


class MockIssueClient:
    """Stand-in for :class:`JiraClient`."""

    def __init__(self) -> None:
        self._epic = _epic()
        self._stories = _stories()

    def get_epic(self, epic_key: str) -> Epic:
        epic = self._epic.model_copy()
        epic.key = epic_key
        return epic

    def get_stories(self, epic_key: str) -> list[Story]:
        return [s.model_copy(deep=True) for s in self._stories]


class MockPullRequestClient:
    """Stand-in for :class:`GitHubClient`. PRs are already attached to mock
    stories, so this client simply echoes them back per issue key."""

    def __init__(self) -> None:
        self._by_key = {s.key: s.pull_requests for s in _stories()}

    def find_pull_requests(self, issue_key: str) -> list[PullRequest]:
        return [pr.model_copy(deep=True) for pr in self._by_key.get(issue_key, [])]


class MockQualityClient:
    """Stand-in quality source."""

    def get_quality_metrics(self) -> QualityMetrics:
        return _quality()
