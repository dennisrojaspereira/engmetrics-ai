"""Analysis orchestration.

``AnalysisService`` is the single entry point that wires the data sources to the
metric/risk calculations and returns a fully populated :class:`EpicReport`. It
depends only on the source *protocols*, so the CLI passes real HTTP clients, the
test suite passes fakes, and a future web API / agent can reuse it verbatim.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path

from ai_engineering_metrics.config import GitHubConfig, Settings
from ai_engineering_metrics.domain import metrics, risk
from ai_engineering_metrics.domain.models import EpicReport, QualityMetrics
from ai_engineering_metrics.integrations.base import (
    IssueSource,
    PullRequestSource,
    QualitySource,
)
from ai_engineering_metrics.integrations.github_client import GitHubClient, detect_current_repo
from ai_engineering_metrics.integrations.jira_client import JiraClient
from ai_engineering_metrics.integrations.quality_client import (
    JsonQualityClient,
    NullQualityClient,
)
from ai_engineering_metrics.mock.mock_data import (
    MockIssueClient,
    MockPullRequestClient,
    MockQualityClient,
)

logger = logging.getLogger("ai_engineering_metrics")


class AnalysisService:
    def __init__(
        self,
        settings: Settings,
        issue_source: IssueSource,
        pr_source: PullRequestSource,
        quality_source: QualitySource,
    ) -> None:
        self._settings = settings
        self._issues = issue_source
        self._prs = pr_source
        self._quality = quality_source

    # ------------------------------------------------------------- factories
    @classmethod
    def for_settings(cls, settings: Settings, *, mock: bool = False) -> AnalysisService:
        """Build a service from configuration, choosing real vs mock clients."""
        if mock or settings.mock_mode:
            logger.info("Running in MOCK mode (no JIRA/GitHub calls).")
            return cls(
                settings,
                MockIssueClient(),
                MockPullRequestClient(),
                MockQualityClient(),
            )

        quality: QualitySource
        if settings.quality_metrics_file:
            quality = JsonQualityClient(settings.quality_metrics_file)
        else:
            quality = NullQualityClient()

        # JIRA always resolves the epic + stories. Pull requests come from the
        # gh CLI; the target repo is taken from .env, or — if unset — auto-detected
        # from the current directory's git remote (machine-CLI style). If neither
        # is available, fall back to JIRA's development panel.
        jira = JiraClient(settings.jira)
        github = settings.github
        if not github.is_configured:
            detected = detect_current_repo()
            if detected:
                owner, name = detected
                github = GitHubConfig(org=owner, repositories=[name], search_all_repos=False)
                logger.info("Auto-detected GitHub repo %s/%s from current directory.", owner, name)

        if github.is_configured:
            scope = (
                github.org
                if github.search_all_repos
                else "/".join(f"{github.org}/{r}" for r in github.repositories)
            )
            logger.info("Using gh CLI for pull-request discovery (%s).", scope or github.org)
            pr_source: PullRequestSource = GitHubClient(github)
        else:
            logger.info("No GitHub repo configured/detected; using JIRA development panel.")
            pr_source = jira
        return cls(settings, jira, pr_source, quality)

    # ---------------------------------------------------------------- analyse
    def analyze(self, epic_key: str) -> EpicReport:
        logger.info("Fetching epic %s", epic_key)
        epic = self._issues.get_epic(epic_key)

        logger.info("Fetching stories for %s", epic_key)
        stories = self._issues.get_stories(epic_key)
        logger.info("Found %d stories", len(stories))

        # A PR may reference more than one issue key; attach each PR to only the
        # first story that claims it so it is never double-counted.
        seen_prs: set[tuple[str, int]] = set()
        for story in stories:
            unique = []
            for pr in self._prs.find_pull_requests(story.key):
                kid = (pr.repository, pr.number)
                if kid in seen_prs:
                    continue
                seen_prs.add(kid)
                unique.append(pr)
            story.pull_requests = unique
            logger.info("Story %s -> %d PR(s)", story.key, len(story.pull_requests))

        # PRs that reference the epic key directly (common when work is committed
        # against the epic rather than an individual story). Dedupe against the
        # PRs already attached to stories.
        epic_prs = [
            pr
            for pr in self._prs.find_pull_requests(epic_key)
            if (pr.repository, pr.number) not in seen_prs
        ]
        logger.info("Epic %s -> %d additional PR(s)", epic_key, len(epic_prs))

        # Derive estimates from story points when JIRA has no estimate fields.
        self._apply_simulated_story_points(stories)
        self._apply_estimates(stories)

        all_prs = [pr for s in stories for pr in s.pull_requests] + epic_prs
        self._apply_pr_simulation(all_prs)
        quality = self._aggregate_pr_quality(all_prs, self._safe_quality())

        productivity = metrics.compute_productivity(stories)
        ai_usage = metrics.compute_ai_usage(
            stories, self._settings.pricing, extra_pull_requests=epic_prs
        )
        rework = metrics.compute_rework(stories, extra_pull_requests=epic_prs)
        epic_risk = risk.compute_epic_risk(stories, ai_usage, quality, rework)

        story_risks = [risk.compute_story_risk(s, quality) for s in stories]
        pr_risks = [
            risk.compute_pr_risk(pr, s.ai_tokens, quality)
            for s in stories
            for pr in s.pull_requests
        ]
        # Epic-level PRs have no single owning story; attribute zero per-PR tokens.
        pr_risks.extend(risk.compute_pr_risk(pr, 0, quality) for pr in epic_prs)

        return EpicReport(
            generated_at=datetime.now(UTC),
            epic=epic,
            stories=stories,
            quality=quality,
            productivity=productivity,
            ai_usage=ai_usage,
            rework=rework,
            risk=epic_risk,
            story_risks=story_risks,
            pr_risks=pr_risks,
            epic_pull_requests=epic_prs,
        )

    def _apply_simulated_story_points(self, stories: list) -> None:
        """Fill story points from a simulation JSON when JIRA has none.
        Real JIRA story points are never overwritten."""
        path = self._settings.estimation.story_points_file
        if not path:
            return
        file = Path(path)
        if not file.exists():
            logger.warning("STORY_POINTS_FILE not found: %s", file)
            return
        try:
            mapping = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            logger.warning("Invalid STORY_POINTS_FILE JSON: %s", exc)
            return
        for s in stories:
            if s.story_points is None and s.key in mapping:
                s.story_points = float(mapping[s.key])

    def _apply_pr_simulation(self, prs: list) -> None:
        """Inject simulated review/rework signals (demo only) from a JSON file.
        Used because some signals (e.g. self-review approvals) can't be produced
        for real on GitHub."""
        from datetime import timedelta

        path = self._settings.estimation.pr_simulation_file
        if not path:
            return
        file = Path(path)
        if not file.exists():
            logger.warning("PR_SIMULATION_FILE not found: %s", file)
            return
        try:
            sim = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            logger.warning("Invalid PR_SIMULATION_FILE JSON: %s", exc)
            return

        direct = {
            "review_cycles",
            "review_comments",
            "requested_changes",
            "commits_after_review",
            "reverts_detected",
            "reviewers",
        }
        for pr in prs:
            ov = sim.get(f"{pr.repository}#{pr.number}") or sim.get(str(pr.number))
            if not ov:
                continue
            for field in direct:
                if field in ov:
                    setattr(pr, field, ov[field])
            ttm = ov.get("time_to_merge_hours")
            if ttm is not None and pr.created_at and pr.merged_at is None:
                pr.status = "merged"
                pr.merged_at = pr.created_at + timedelta(hours=float(ttm))

    def _apply_estimates(self, stories: list) -> None:
        """When JIRA lacks estimate fields, derive them from story points:
        without-AI = SP * story_point_hours; with-AI applies the savings %."""
        est = self._settings.estimation
        for s in stories:
            if s.estimate_without_ai_hours <= 0 and s.story_points:
                without = s.story_points * est.story_point_hours
                s.estimate_without_ai_hours = round(without, 2)
                s.estimate_with_ai_hours = round(without * (1 - est.ai_savings_percent / 100), 2)

    @staticmethod
    def _aggregate_pr_quality(all_prs: list, base: QualityMetrics) -> QualityMetrics:
        """Fill the epic Code-quality section from per-PR diff heuristics when no
        dedicated quality source (JSON/SonarQube) is configured."""
        qs = [pr.code_quality for pr in all_prs if pr.code_quality]
        if base.source != "unavailable" or not qs:
            return base
        n = len(qs)
        with_tests = sum(1 for q in qs if q.has_tests)
        return QualityMetrics(
            cyclomatic_complexity=round(sum(q.branch_keywords_added for q in qs) / n, 1),
            cognitive_complexity=round(sum(q.nesting_score for q in qs) / n, 1),
            duplication_percent=None,
            code_smells=sum(q.code_smells for q in qs),
            static_bugs=sum(q.debug_statements for q in qs),
            vulnerabilities=0,
            test_coverage_percent=round(with_tests / n * 100, 1),
            source="pr-heuristic",
        )

    def _safe_quality(self) -> QualityMetrics:
        try:
            return self._quality.get_quality_metrics()
        except Exception as exc:  # quality is optional; never fail the whole run
            logger.warning("Quality metrics unavailable: %s", exc)
            return QualityMetrics(source="unavailable")

    def close(self) -> None:
        for source in (self._issues, self._prs):
            close = getattr(source, "close", None)
            if callable(close):
                close()
