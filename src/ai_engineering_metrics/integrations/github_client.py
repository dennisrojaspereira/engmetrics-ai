"""GitHub client backed by the ``gh`` CLI.

Instead of managing a ``GITHUB_TOKEN`` and calling the REST API directly, this
client shells out to the official `GitHub CLI <https://cli.github.com>`_, which
handles authentication on its own (``gh auth login``). It discovers pull
requests related to a JIRA issue key (by key in title/body, and by branch name
for the configured repositories) and enriches each PR with diff and review data
via ``gh pr view --json``.

No tokens are read or logged by this module.
"""

from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
from datetime import datetime
from typing import Any

from ai_engineering_metrics.config import GitHubConfig
from ai_engineering_metrics.domain.models import PRCodeQuality, PullRequest
from ai_engineering_metrics.integrations.base import IntegrationError

logger = logging.getLogger("ai_engineering_metrics")

REVERT_RE = re.compile(r"\brevert\b", re.IGNORECASE)
_GH_TIMEOUT = 60  # seconds per gh invocation

# Fields requested from `gh pr view`; one call returns everything we need.
_PR_VIEW_FIELDS = ",".join(
    [
        "number",
        "title",
        "author",
        "headRefName",
        "state",
        "createdAt",
        "mergedAt",
        "additions",
        "deletions",
        "changedFiles",
        "commits",
        "reviews",
        "comments",
        "body",
        "url",
    ]
)

# Diff-analysis heuristics ----------------------------------------------------
_BRANCH_RE = re.compile(r"\b(if|else if|elif|for|while|case|catch|switch)\b|&&|\|\||\?\s")
_TODO_RE = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")
_DEBUG_RE = re.compile(
    r"console\.(log|debug)|debugger|System\.out\.print|fmt\.Print|var_dump|\bprint\(",
)
_TEST_PATH_RE = re.compile(r"(^|/)(test|tests|spec|__tests__)/|\.(test|spec)\.", re.IGNORECASE)
_LONG_LINE = 120


def analyze_diff(diff_text: str) -> PRCodeQuality:
    """Compute heuristic code-quality signals from a unified diff."""
    q = PRCodeQuality()
    files: set[str] = set()
    test_files: set[str] = set()
    for raw in diff_text.splitlines():
        if raw.startswith("+++ b/") or raw.startswith("--- a/"):
            path = raw[6:]
            if path and path != "/dev/null":
                files.add(path)
                if _TEST_PATH_RE.search(path):
                    test_files.add(path)
            continue
        if raw.startswith("+") and not raw.startswith("+++"):
            line = raw[1:]
            q.added_lines += 1
            q.branch_keywords_added += len(_BRANCH_RE.findall(line))
            if len(line) > _LONG_LINE:
                q.long_lines += 1
            if _TODO_RE.search(line):
                q.todos_added += 1
            if _DEBUG_RE.search(line):
                q.debug_statements += 1
            indent = len(line) - len(line.lstrip(" \t"))
            if indent >= 12:  # deeply nested added code (~3+ levels)
                q.nesting_score += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            q.removed_lines += 1

    q.files_changed = len(files)
    q.test_files_touched = len(test_files)
    q.has_tests = bool(test_files)

    # Human-readable notes explaining what was evaluated / found.
    q.notes.append(
        f"{q.added_lines} added / {q.removed_lines} removed lines across {q.files_changed} file(s)."
    )
    q.notes.append(
        f"Control-flow keywords added: {q.branch_keywords_added} (cyclomatic-complexity proxy)."
    )
    q.notes.append(f"Deeply-nested added lines: {q.nesting_score} (cognitive-complexity proxy).")
    if q.debug_statements:
        q.notes.append(f"⚠ {q.debug_statements} debug/print statement(s) added.")
    if q.todos_added:
        q.notes.append(f"⚠ {q.todos_added} TODO/FIXME marker(s) added.")
    if q.long_lines:
        q.notes.append(f"{q.long_lines} line(s) longer than {_LONG_LINE} chars.")
    q.notes.append("Tests touched ✓" if q.has_tests else "⚠ No test files touched in this PR.")
    return q


def detect_current_repo() -> tuple[str, str] | None:
    """Detect ``(owner, repo)`` from the current directory via the gh CLI.

    Lets the tool behave like a machine-wide CLI: ``cd`` into a checkout and run
    ``analyze`` — the GitHub repo is inferred from the git remote, so no
    GITHUB_ORG/GITHUB_REPOSITORIES is needed in .env. Returns ``None`` when not
    inside a GitHub repo or when gh is unavailable.
    """
    gh = shutil.which("gh")
    if not gh:
        return None
    try:
        result = subprocess.run(
            [gh, "repo", "view", "--json", "owner,name"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=_GH_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    owner = (data.get("owner") or {}).get("login")
    name = data.get("name")
    return (owner, name) if owner and name else None


def _mentions_key(text: str, issue_key: str) -> bool:
    """True if ``issue_key`` appears as a distinct token in ``text``.

    GitHub's search tokenizes on hyphens, so a query for ``KAN-5`` also matches
    PRs that merely contain "KAN" and "5" (e.g. "TypeScript 5.8.x [KAN-4]"). We
    re-check the literal key with boundaries so ``KAN-5`` matches "[KAN-5]" but
    not "KAN-50" or "5.8.x".
    """
    pattern = rf"(?<![A-Za-z0-9-]){re.escape(issue_key)}(?!\d)"
    return re.search(pattern, text, re.IGNORECASE) is not None


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class GitHubClient:
    """Finds and enriches pull requests using the ``gh`` CLI."""

    def __init__(self, config: GitHubConfig) -> None:
        if not config.is_configured:
            raise IntegrationError(
                "GitHub is not configured. Set GITHUB_ORG (and authenticate the "
                "gh CLI with `gh auth login`), or run in --mock mode."
            )
        self._config = config
        self._ensure_gh_ready()

    # ------------------------------------------------------------ gh plumbing
    @staticmethod
    def _gh_path() -> str:
        path = shutil.which("gh")
        if not path:
            raise IntegrationError(
                "The GitHub CLI (`gh`) was not found on PATH. Install it from "
                "https://cli.github.com and run `gh auth login`."
            )
        return path

    def _ensure_gh_ready(self) -> None:
        gh = self._gh_path()
        result = subprocess.run(
            [gh, "auth", "status"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=_GH_TIMEOUT,
        )
        if result.returncode != 0:
            raise IntegrationError(
                "GitHub CLI is not authenticated. Run `gh auth login` and try again."
            )

    def _run_json(self, args: list[str]) -> Any:
        """Run a gh command expected to emit JSON; returns parsed data."""
        gh = self._gh_path()
        try:
            result = subprocess.run(
                [gh, *args],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=_GH_TIMEOUT,
            )
        except subprocess.TimeoutExpired as exc:
            raise IntegrationError(f"gh command timed out: gh {' '.join(args)}") from exc

        if result.returncode != 0:
            # stderr from gh may include rate-limit guidance; it never contains
            # our secrets, so it is safe to surface (trimmed).
            stderr = (result.stderr or "").strip().splitlines()
            detail = stderr[-1] if stderr else f"exit code {result.returncode}"
            if "rate limit" in detail.lower():
                raise IntegrationError(f"GitHub rate limit hit via gh: {detail}")
            raise IntegrationError(f"gh command failed ({detail})")

        if not result.stdout.strip():
            return []
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise IntegrationError(f"Could not parse gh JSON output: {exc}") from exc

    def _run_text(self, args: list[str]) -> str:
        """Run a gh command and return raw stdout (e.g. a diff).

        Best-effort: used only for optional enrichment (the PR diff), so it
        degrades to an empty string if gh is unavailable or the call fails,
        rather than raising.
        """
        gh = shutil.which("gh")
        if not gh:
            return ""
        try:
            result = subprocess.run(
                [gh, *args], capture_output=True, text=True, encoding="utf-8", timeout=_GH_TIMEOUT
            )
        except subprocess.TimeoutExpired:
            return ""
        return result.stdout if result.returncode == 0 else ""

    # ------------------------------------------------------------- discovery
    def find_pull_requests(self, issue_key: str) -> list[PullRequest]:
        """Return PRs that reference ``issue_key`` in title/body or branch."""
        seen: dict[str, dict[str, Any]] = {}

        # 1) Full-text search across PR title + body.
        for item in self._search_prs(issue_key):
            repo = (item.get("repository") or {}).get("nameWithOwner")
            number = item.get("number")
            if repo and number is not None:
                seen[f"{repo}#{number}"] = {"repo": repo, "number": number}

        # 2) Branch-name match for explicitly configured repositories.
        for repo in self._target_repos():
            for number in self._branch_matches(repo, issue_key):
                seen.setdefault(f"{repo}#{number}", {"repo": repo, "number": number})

        results: list[PullRequest] = []
        for ref in seen.values():
            pr = self._load_pull_request(ref["repo"], ref["number"], issue_key)
            if pr is not None:
                results.append(pr)
        return results

    def _search_prs(self, issue_key: str) -> list[dict[str, Any]]:
        # `--owner` works for both organizations and personal accounts.
        items = self._run_json(
            [
                "search",
                "prs",
                issue_key,
                "--owner",
                self._config.org,
                "--json",
                "number,repository",
                "--limit",
                "50",
            ]
        )
        if self._config.search_all_repos or not self._config.repositories:
            return items
        allowed = {f"{self._config.org}/{name}" for name in self._config.repositories}
        return [it for it in items if (it.get("repository") or {}).get("nameWithOwner") in allowed]

    def _branch_matches(self, repo: str, issue_key: str) -> list[int]:
        prs = self._run_json(
            [
                "pr",
                "list",
                "--repo",
                repo,
                "--state",
                "all",
                "--limit",
                "100",
                "--json",
                "number,headRefName",
            ]
        )
        return [
            pr["number"] for pr in prs if issue_key.lower() in (pr.get("headRefName") or "").lower()
        ]

    # -------------------------------------------------------------- enrich PR
    def _load_pull_request(self, repo: str, number: int, issue_key: str) -> PullRequest | None:
        try:
            detail = self._run_json(
                ["pr", "view", str(number), "--repo", repo, "--json", _PR_VIEW_FIELDS]
            )
        except IntegrationError as exc:
            logger.warning("Skipping %s#%s: %s", repo, number, exc)
            return None

        # Reject fuzzy search false positives: the literal key must appear in the
        # title, branch or body.
        haystack = " ".join(
            [detail.get("title", ""), detail.get("headRefName", ""), detail.get("body", "") or ""]
        )
        if not _mentions_key(haystack, issue_key):
            logger.info("Skipping %s#%s: does not literally mention %s", repo, number, issue_key)
            return None

        reviews = detail.get("reviews") or []
        commits = detail.get("commits") or []

        requested_changes = sum(1 for r in reviews if r.get("state") == "CHANGES_REQUESTED")
        review_cycles = sum(
            1 for r in reviews if r.get("state") in {"CHANGES_REQUESTED", "APPROVED"}
        )
        reviewers = sorted({(r.get("author") or {}).get("login", "") for r in reviews} - {""})
        # `gh pr view` exposes review summary comments but not inline-comment
        # counts; the number of non-empty review bodies is a faithful proxy.
        review_comments = sum(1 for r in reviews if (r.get("body") or "").strip())
        commits_after_review = self._commits_after_first_review(reviews, commits)
        reverts = sum(1 for c in commits if REVERT_RE.search(_commit_message(c)))

        state = (detail.get("state") or "OPEN").lower()
        status = "merged" if detail.get("mergedAt") else state

        # Per-PR code-quality evaluation from the diff.
        diff = self._run_text(["pr", "diff", str(number), "--repo", repo])
        code_quality = analyze_diff(diff) if diff else None

        return PullRequest(
            number=detail.get("number", number),
            title=detail.get("title", ""),
            author=(detail.get("author") or {}).get("login", "unknown"),
            repository=repo,
            branch=detail.get("headRefName", ""),
            status=status,
            url=detail.get("url"),
            created_at=_parse_dt(detail.get("createdAt")),
            merged_at=_parse_dt(detail.get("mergedAt")),
            commits=len(commits),
            changed_files=detail.get("changedFiles", 0),
            additions=detail.get("additions", 0),
            deletions=detail.get("deletions", 0),
            review_comments=review_comments,
            requested_changes=requested_changes,
            review_cycles=review_cycles,
            commits_after_review=commits_after_review,
            reverts_detected=reverts,
            reviewers=reviewers,
            code_quality=code_quality,
        )

    @staticmethod
    def _commits_after_first_review(
        reviews: list[dict[str, Any]], commits: list[dict[str, Any]]
    ) -> int:
        review_dates = [dt for r in reviews if (dt := _parse_dt(r.get("submittedAt"))) is not None]
        if not review_dates:
            return 0
        first_review = min(review_dates)
        count = 0
        for c in commits:
            committed = _parse_dt(c.get("committedDate"))
            if committed and committed > first_review:
                count += 1
        return count

    # --------------------------------------------------------------- helpers
    def _target_repos(self) -> list[str]:
        if self._config.search_all_repos or not self._config.repositories:
            return []
        return [f"{self._config.org}/{name}" for name in self._config.repositories]


def _commit_message(commit: dict[str, Any]) -> str:
    headline = commit.get("messageHeadline") or ""
    body = commit.get("messageBody") or ""
    return f"{headline}\n{body}"
