"""Domain models.

These Pydantic models are the single source of truth shared by every layer
(integrations populate them, metrics/risk read them, reports render them and
storage serialises them). They are intentionally I/O-free so they can be reused
unchanged from a CLI, a web API, an agent or a skill.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class User(BaseModel):
    display_name: str
    login: str | None = None  # GitHub / JIRA account id, optional


class PRCodeQuality(BaseModel):
    """Lightweight, diff-based code-quality signals for a single PR.

    These are heuristics computed from the PR diff (not a full static-analysis
    run), enough to flag risky changes and explain what was evaluated.
    """

    files_changed: int = 0
    added_lines: int = 0
    removed_lines: int = 0
    branch_keywords_added: int = 0  # cyclomatic-complexity proxy
    nesting_score: int = 0  # cognitive-complexity proxy
    todos_added: int = 0
    debug_statements: int = 0  # console.log / print / debugger ...
    long_lines: int = 0
    test_files_touched: int = 0
    has_tests: bool = False
    notes: list[str] = Field(default_factory=list)

    @property
    def code_smells(self) -> int:
        return self.todos_added + self.debug_statements + self.long_lines


class PRCheck(BaseModel):
    """One evaluated dimension shown in the per-PR popup."""

    label: str
    value: str
    status: str  # ok | warn | bad | info


class PullRequest(BaseModel):
    number: int
    title: str
    author: str
    repository: str
    branch: str
    status: str  # open | merged | closed
    url: str | None = None
    created_at: datetime | None = None
    merged_at: datetime | None = None
    commits: int = 0
    changed_files: int = 0
    additions: int = 0
    deletions: int = 0
    review_comments: int = 0
    requested_changes: int = 0
    review_cycles: int = 0
    commits_after_review: int = 0
    reverts_detected: int = 0
    reviewers: list[str] = Field(default_factory=list)
    code_quality: PRCodeQuality | None = None

    @property
    def total_changed_lines(self) -> int:
        return self.additions + self.deletions

    @property
    def time_to_merge_hours(self) -> float | None:
        if self.created_at and self.merged_at:
            return round((self.merged_at - self.created_at).total_seconds() / 3600.0, 2)
        return None


class Story(BaseModel):
    key: str
    summary: str
    status: str
    assignee: str | None = None
    labels: list[str] = Field(default_factory=list)
    story_points: float | None = None
    ai_tokens: int = 0
    estimate_without_ai_hours: float = 0.0
    estimate_with_ai_hours: float = 0.0
    created_at: datetime | None = None
    updated_at: datetime | None = None
    resolved_at: datetime | None = None
    pull_requests: list[PullRequest] = Field(default_factory=list)

    @property
    def hours_saved(self) -> float:
        return round(self.estimate_without_ai_hours - self.estimate_with_ai_hours, 2)

    @property
    def lead_time_hours(self) -> float | None:
        if self.created_at and self.resolved_at:
            return round((self.resolved_at - self.created_at).total_seconds() / 3600.0, 2)
        return None

    @property
    def total_changed_lines(self) -> int:
        return sum(pr.total_changed_lines for pr in self.pull_requests)

    @property
    def total_additions(self) -> int:
        return sum(pr.additions for pr in self.pull_requests)


class Epic(BaseModel):
    key: str
    summary: str
    status: str
    assignee: str | None = None
    labels: list[str] = Field(default_factory=list)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class QualityMetrics(BaseModel):
    """Static-analysis quality signals, mocked or imported from JSON."""

    cyclomatic_complexity: float | None = None
    cognitive_complexity: float | None = None
    duplication_percent: float | None = None
    code_smells: int | None = None
    static_bugs: int | None = None
    vulnerabilities: int | None = None
    test_coverage_percent: float | None = None
    source: str = "unavailable"  # mock | json | unavailable


class ProductivityMetrics(BaseModel):
    estimated_hours_without_ai: float = 0.0
    estimated_hours_with_ai: float = 0.0
    hours_saved: float = 0.0
    savings_percent: float = 0.0
    avg_lead_time_hours: float | None = None
    avg_pr_lead_time_hours: float | None = None
    prs_per_story: float = 0.0


class AIUsageMetrics(BaseModel):
    total_tokens: int = 0
    tokens_per_story: float = 0.0
    tokens_per_pr: float = 0.0
    tokens_per_added_line: float = 0.0
    tokens_per_changed_line: float = 0.0
    tokens_per_story_point: float = 0.0
    tokens_per_hour_saved: float = 0.0
    estimated_cost: float = 0.0
    cost_per_story: float = 0.0
    cost_per_pr: float = 0.0
    cost_per_hour_saved: float = 0.0


class ReworkMetrics(BaseModel):
    avg_time_to_merge_hours: float | None = None
    total_review_cycles: int = 0
    total_review_comments: int = 0
    total_requested_changes: int = 0
    total_commits_after_review: int = 0
    reverts_detected: int = 0
    files_touched_again_later: int = 0


class RiskComponent(BaseModel):
    name: str
    weight: float
    normalized: float  # 0..1, where 1 = worst
    contribution: float  # weight * normalized * 100


class RiskScore(BaseModel):
    score: float = 0.0  # 0..100
    level: str = "unknown"  # low | moderate | high | critical
    components: list[RiskComponent] = Field(default_factory=list)


class StoryRisk(BaseModel):
    key: str
    score: float
    level: str


class PullRequestRisk(BaseModel):
    number: int
    repository: str
    title: str
    score: float
    level: str
    components: list[RiskComponent] = Field(default_factory=list)


class EpicReport(BaseModel):
    """The full analysis result. This is what the CLI, API or agent returns."""

    generated_at: datetime
    epic: Epic
    stories: list[Story]
    quality: QualityMetrics
    productivity: ProductivityMetrics
    ai_usage: AIUsageMetrics
    rework: ReworkMetrics
    risk: RiskScore
    story_risks: list[StoryRisk] = Field(default_factory=list)
    pr_risks: list[PullRequestRisk] = Field(default_factory=list)
    # PRs that reference the epic key directly (not tied to a single story).
    epic_pull_requests: list[PullRequest] = Field(default_factory=list)

    @property
    def all_pull_requests(self) -> list[PullRequest]:
        prs = [pr for story in self.stories for pr in story.pull_requests]
        prs.extend(self.epic_pull_requests)
        return prs
