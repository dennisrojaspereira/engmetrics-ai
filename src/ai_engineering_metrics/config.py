"""Application configuration.

Loads values from environment variables (and a ``.env`` file via python-dotenv)
into a validated Pydantic model. Keeping configuration in a single typed object
makes it trivial to reuse the same settings from the CLI today and from a web
API, agent or skill in the future.
"""

from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel, Field


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _as_float(value: str | None, default: float) -> float:
    if value is None or value.strip() == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


def _as_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


class JiraConfig(BaseModel):
    base_url: str = ""
    email: str = ""
    api_token: str = Field(default="", repr=False)  # never echo secrets
    epic_link_field: str = "customfield_10014"
    ai_tokens_field: str = "customfield_10100"
    estimate_without_ai_field: str = "customfield_10101"
    estimate_with_ai_field: str = "customfield_10102"
    story_points_field: str = "customfield_10016"

    @property
    def is_configured(self) -> bool:
        return bool(self.base_url and self.email and self.api_token)


class GitHubConfig(BaseModel):
    # Authentication is handled by the `gh` CLI (`gh auth login`), so no token is
    # stored here. Only the org and repo scope are configuration.
    org: str = ""
    repositories: list[str] = Field(default_factory=list)
    search_all_repos: bool = True

    @property
    def is_configured(self) -> bool:
        return bool(self.org)


class PricingConfig(BaseModel):
    input_per_1m: float = 3.00
    output_per_1m: float = 15.00
    default_per_1m: float = 6.00


class EstimationConfig(BaseModel):
    """Fallback estimation when JIRA has no with/without-AI estimate fields.

    estimate_without_ai = story_points * story_point_hours
    estimate_with_ai    = estimate_without_ai * (1 - ai_savings_percent/100)

    ``story_points_file`` optionally supplies simulated story points per issue
    key (JSON: {"KAN-5": 3, ...}) for JIRA projects that have no story-points
    field enabled. Real JIRA story points always take precedence.
    """

    story_point_hours: float = 1.0
    ai_savings_percent: float = 40.0
    story_points_file: str | None = None
    # Optional demo simulation of PR review/rework signals that cannot be
    # produced for real (e.g. self-review is blocked on GitHub). JSON keyed by
    # PR number or "repo#number": {"review_cycles", "review_comments",
    # "requested_changes", "commits_after_review", "reverts_detected",
    # "time_to_merge_hours", "reviewers"}.
    pr_simulation_file: str | None = None


class Settings(BaseModel):
    """Top-level, fully validated configuration object."""

    mock_mode: bool = False
    quality_metrics_file: str | None = None
    jira: JiraConfig = Field(default_factory=JiraConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    pricing: PricingConfig = Field(default_factory=PricingConfig)
    estimation: EstimationConfig = Field(default_factory=EstimationConfig)

    @classmethod
    def from_env(cls, *, load_dotenv_file: bool = True) -> Settings:
        if load_dotenv_file:
            load_dotenv()

        jira = JiraConfig(
            base_url=os.getenv("JIRA_BASE_URL", "").rstrip("/"),
            email=os.getenv("JIRA_EMAIL", ""),
            api_token=os.getenv("JIRA_API_TOKEN", ""),
            epic_link_field=os.getenv("JIRA_EPIC_LINK_FIELD", "customfield_10014"),
            ai_tokens_field=os.getenv("JIRA_AI_TOKENS_FIELD", "customfield_10100"),
            estimate_without_ai_field=os.getenv(
                "JIRA_ESTIMATE_WITHOUT_AI_FIELD", "customfield_10101"
            ),
            estimate_with_ai_field=os.getenv("JIRA_ESTIMATE_WITH_AI_FIELD", "customfield_10102"),
            story_points_field=os.getenv("JIRA_STORY_POINTS_FIELD", "customfield_10016"),
        )

        github = GitHubConfig(
            org=os.getenv("GITHUB_ORG", ""),
            repositories=_as_list(os.getenv("GITHUB_REPOSITORIES")),
            search_all_repos=_as_bool(os.getenv("GITHUB_SEARCH_ALL_REPOS"), default=True),
        )

        pricing = PricingConfig(
            input_per_1m=_as_float(os.getenv("AI_TOKEN_PRICE_INPUT_PER_1M"), 3.00),
            output_per_1m=_as_float(os.getenv("AI_TOKEN_PRICE_OUTPUT_PER_1M"), 15.00),
            default_per_1m=_as_float(os.getenv("DEFAULT_TOKEN_PRICE_PER_1M"), 6.00),
        )

        estimation = EstimationConfig(
            story_point_hours=_as_float(os.getenv("STORY_POINT_HOURS"), 1.0),
            ai_savings_percent=_as_float(os.getenv("AI_SAVINGS_PERCENT"), 40.0),
            story_points_file=os.getenv("STORY_POINTS_FILE") or None,
            pr_simulation_file=os.getenv("PR_SIMULATION_FILE") or None,
        )

        return cls(
            mock_mode=_as_bool(os.getenv("MOCK_MODE"), default=False),
            quality_metrics_file=os.getenv("QUALITY_METRICS_FILE") or None,
            jira=jira,
            github=github,
            pricing=pricing,
            estimation=estimation,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached accessor so the whole process shares one Settings instance."""
    return Settings.from_env()
