"""JIRA client.

Resolves an epic, the stories linked to it, and the pull requests linked to each
issue via JIRA's *development information* panel (the same PRs you see under
"Development" on an issue). Uses the current JIRA Cloud REST API:

* ``GET  /rest/api/3/issue/{key}`` — epic / issue details
* ``POST /rest/api/3/search/jql`` — token-paginated issue search (the legacy
  ``GET /search`` was removed by Atlassian)
* ``GET  /rest/dev-status/1.0/issue/detail`` — pull requests linked to an issue

Custom field ids (AI tokens, estimates, story points, epic link) come from
configuration, so the tool works against any JIRA instance.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from ai_engineering_metrics.config import JiraConfig
from ai_engineering_metrics.domain.models import Epic, PullRequest, Story
from ai_engineering_metrics.integrations.base import HttpClient, IntegrationError, NotFoundError

logger = logging.getLogger("ai_engineering_metrics")

# JIRA status names are localized (e.g. "A fazer", "Em andamento"). The status
# *category* key is language-independent, so we map it to a stable English label
# to keep the whole report in English regardless of the JIRA UI language.
_STATUS_CATEGORY_EN = {
    "new": "To Do",
    "indeterminate": "In Progress",
    "done": "Done",
}


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _as_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


class JiraClient:
    """Reads epics, their stories and linked PRs from JIRA Cloud."""

    def __init__(self, config: JiraConfig) -> None:
        if not config.is_configured:
            raise IntegrationError(
                "JIRA is not configured. Set JIRA_BASE_URL, JIRA_EMAIL and "
                "JIRA_API_TOKEN, or run in --mock mode."
            )
        self._config = config
        self._http = HttpClient(
            base_url=f"{config.base_url}/rest/api/3",
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            auth=(config.email, config.api_token),
        )
        # The dev-status endpoint lives outside /rest/api/3.
        self._dev = HttpClient(
            base_url=f"{config.base_url}/rest/dev-status/1.0",
            headers={"Accept": "application/json"},
            auth=(config.email, config.api_token),
        )

    def close(self) -> None:
        self._http.close()
        self._dev.close()

    def __enter__(self) -> JiraClient:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    # ------------------------------------------------------------------ epic
    def get_epic(self, epic_key: str) -> Epic:
        try:
            response = self._http.get(f"/issue/{epic_key}", params={"fields": "*all"})
        except NotFoundError as exc:
            raise NotFoundError(f"Epic {epic_key} does not exist in JIRA.") from exc

        data = response.json()
        self._issue_ids = getattr(self, "_issue_ids", {})
        self._issue_ids[epic_key] = data.get("id", "")
        fields = data.get("fields", {})
        return Epic(
            key=epic_key,
            summary=fields.get("summary", ""),
            status=self._status(fields),
            assignee=self._assignee(fields),
            labels=fields.get("labels", []) or [],
            created_at=_parse_dt(fields.get("created")),
            updated_at=_parse_dt(fields.get("updated")),
        )

    # --------------------------------------------------------------- stories
    def get_stories(self, epic_key: str) -> list[Story]:
        fields = self._story_fields()
        # Try the modern parent link first, then the configured epic-link field.
        candidates = [
            f'parent = "{epic_key}"',
            f'"{self._config.epic_link_field}" = "{epic_key}"',
        ]
        last_error: Exception | None = None
        for jql in candidates:
            try:
                issues = self._search(jql, fields)
            except IntegrationError as exc:
                last_error = exc  # e.g. JQL field not present in this project
                continue
            if issues:
                return [self._to_story(i) for i in issues]
        if last_error is not None and not self._search_ok:
            logger.warning("Story search fell back without results: %s", last_error)
        return []

    def _search(self, jql: str, fields: list[str]) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        next_token: str | None = None
        self._search_ok = False
        while True:
            body: dict[str, Any] = {"jql": jql, "maxResults": 100, "fields": fields}
            if next_token:
                body["nextPageToken"] = next_token
            payload = self._http.post("/search/jql", json=body).json()
            self._search_ok = True
            issues.extend(payload.get("issues", []))
            next_token = payload.get("nextPageToken")
            if payload.get("isLast", True) or not next_token:
                break
        return issues

    def _story_fields(self) -> list[str]:
        cfg = self._config
        fields = [
            "summary",
            "status",
            "issuetype",
            "assignee",
            "labels",
            "created",
            "updated",
            "resolutiondate",
            cfg.ai_tokens_field,
            cfg.estimate_without_ai_field,
            cfg.estimate_with_ai_field,
            cfg.story_points_field,
        ]
        # Drop unconfigured (empty) custom-field ids so the search API accepts it.
        return [f for f in fields if f]

    def _to_story(self, issue: dict[str, Any]) -> Story:
        fields = issue.get("fields", {})
        cfg = self._config
        self._issue_ids = getattr(self, "_issue_ids", {})
        self._issue_ids[issue.get("key", "")] = issue.get("id", "")
        return Story(
            key=issue.get("key", ""),
            summary=fields.get("summary", ""),
            status=self._status(fields),
            assignee=self._assignee(fields),
            labels=fields.get("labels", []) or [],
            story_points=_as_float(fields.get(cfg.story_points_field)) or None,
            ai_tokens=_as_int(fields.get(cfg.ai_tokens_field)),
            estimate_without_ai_hours=_as_float(fields.get(cfg.estimate_without_ai_field)),
            estimate_with_ai_hours=_as_float(fields.get(cfg.estimate_with_ai_field)),
            created_at=_parse_dt(fields.get("created")),
            updated_at=_parse_dt(fields.get("updated")),
            resolved_at=_parse_dt(fields.get("resolutiondate")),
        )

    @staticmethod
    def _assignee(fields: dict[str, Any]) -> str | None:
        assignee = fields.get("assignee")
        if assignee:
            return assignee.get("displayName")
        return None

    @staticmethod
    def _status(fields: dict[str, Any]) -> str:
        status = fields.get("status") or {}
        category = (status.get("statusCategory") or {}).get("key")
        if category in _STATUS_CATEGORY_EN:
            return _STATUS_CATEGORY_EN[category]
        return status.get("name", "Unknown")

    # --------------------------------------------------- pull requests (dev)
    def find_pull_requests(self, issue_key: str) -> list[PullRequest]:
        """Return PRs linked to ``issue_key`` in JIRA's development panel."""
        issue_id = self._resolve_id(issue_key)
        if not issue_id:
            return []
        try:
            response = self._dev.get(
                "/issue/detail",
                params={
                    "issueId": issue_id,
                    "applicationType": "GitHub",
                    "dataType": "pullrequest",
                },
            )
        except IntegrationError as exc:
            logger.warning("Dev-status lookup failed for %s: %s", issue_key, exc)
            return []

        details = response.json().get("detail", [])
        prs: list[PullRequest] = []
        for block in details:
            for pr in block.get("pullRequests", []):
                prs.append(self._to_pull_request(pr))
        return prs

    def _resolve_id(self, issue_key: str) -> str:
        self._issue_ids = getattr(self, "_issue_ids", {})
        if issue_key in self._issue_ids:
            return self._issue_ids[issue_key]
        try:
            data = self._http.get(f"/issue/{issue_key}", params={"fields": "id"}).json()
        except IntegrationError:
            return ""
        issue_id = data.get("id", "")
        self._issue_ids[issue_key] = issue_id
        return issue_id

    @staticmethod
    def _to_pull_request(pr: dict[str, Any]) -> PullRequest:
        # JIRA's dev panel exposes a limited set of fields (no diff/review
        # counts). We map what is available; the rest stays at zero.
        raw_id = str(pr.get("id", "0")).lstrip("#")
        number = _as_int(raw_id)
        status = (pr.get("status") or "OPEN").lower()
        if status == "declined":
            status = "closed"
        repository = (pr.get("repositoryName") or pr.get("name") or "").strip()
        source_branch = (pr.get("source") or {}).get("branch", "")
        return PullRequest(
            number=number,
            title=pr.get("name", ""),
            author=(pr.get("author") or {}).get("name", "unknown"),
            repository=repository,
            branch=source_branch,
            status="merged" if status == "merged" else status,
            created_at=_parse_dt(pr.get("lastUpdate")),
            merged_at=_parse_dt(pr.get("lastUpdate")) if status == "merged" else None,
            # commits / additions / deletions are not exposed by the dev panel.
            review_comments=_as_int(pr.get("commentCount")),
            reviewers=[r.get("name", "") for r in pr.get("reviewers", []) if r.get("name")],
        )
