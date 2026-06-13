"""HTML dashboard renderer.

Renders an :class:`EpicReport` into a self-contained HTML file using Jinja2 for
layout and Plotly for the charts. Only Plotly.js is fetched from a CDN; the rest
of the file is fully local.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ai_engineering_metrics.domain.models import EpicReport, PullRequest
from ai_engineering_metrics.reports import charts

_TEMPLATE_DIR = Path(__file__).parent / "templates"


def _fmt_int(value: Any) -> str:
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return "-"


def _fmt_float(value: Any, digits: int = 1) -> str:
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return "-"


def _fmt_money(value: Any) -> str:
    try:
        return f"${float(value):,.2f}"
    except (TypeError, ValueError):
        return "-"


def _build_env() -> Environment:
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    env.filters["int_"] = _fmt_int
    env.filters["f1"] = lambda v: _fmt_float(v, 1)
    env.filters["f2"] = lambda v: _fmt_float(v, 2)
    env.filters["money"] = _fmt_money
    return env


def _pr_key(repo: str, number: int) -> str:
    return f"{repo}#{number}"


def _metric(label: str, value: object, status: str, tip: str) -> dict:
    return {"label": label, "value": value, "status": status, "tip": tip}


def _quality_metrics(pr: PullRequest) -> list[dict]:
    """Per-PR code-quality metrics, each with an improvement tooltip."""
    q = pr.code_quality
    if not q:
        return []
    return [
        _metric(
            "Change size",
            f"+{pr.additions} / -{pr.deletions}",
            "warn" if pr.total_changed_lines > 800 else "ok",
            "Total lines changed. Large PRs are harder to review — split into smaller PRs.",
        ),
        _metric(
            "Cyclomatic proxy",
            q.branch_keywords_added,
            "warn" if q.branch_keywords_added > 40 else "ok",
            "Control-flow keywords (if/for/while) added. High = complex logic; extract functions.",
        ),
        _metric(
            "Cognitive proxy",
            q.nesting_score,
            "warn" if q.nesting_score > 20 else "ok",
            "Deeply-nested added lines. Reduce nesting with early returns / guard clauses.",
        ),
        _metric(
            "Code smells",
            q.code_smells,
            "warn" if q.code_smells > 0 else "ok",
            "TODO/FIXME + debug statements + long lines combined. Clean these up before merging.",
        ),
        _metric(
            "Debug statements",
            q.debug_statements,
            "bad" if q.debug_statements else "ok",
            "console.log / print / debugger left in the code. Remove them before merge.",
        ),
        _metric(
            "TODO / FIXME",
            q.todos_added,
            "warn" if q.todos_added else "ok",
            "Unfinished-work markers added. Resolve them or track as follow-up issues.",
        ),
        _metric(
            "Long lines",
            q.long_lines,
            "warn" if q.long_lines else "ok",
            "Lines longer than 120 chars hurt readability. Wrap or refactor them.",
        ),
        _metric(
            "Tests touched",
            "yes" if q.has_tests else "no",
            "ok" if q.has_tests else "bad",
            "Whether test files were changed. Add or update tests to cover the new code.",
        ),
    ]


def _rework_metrics(pr: PullRequest) -> list[dict]:
    """Per-PR rework metrics, each with an improvement tooltip."""
    ttm = f"{pr.time_to_merge_hours} h" if pr.time_to_merge_hours is not None else "not merged"
    return [
        _metric(
            "Time to merge",
            ttm,
            "info" if pr.time_to_merge_hours is not None else "warn",
            "Hours from opened to merged. Long times can signal blockers or oversized PRs.",
        ),
        _metric(
            "Review cycles",
            pr.review_cycles,
            "warn" if pr.review_cycles > 3 else "ok",
            "Approved / changes-requested events. Many cycles → unclear scope or a large PR.",
        ),
        _metric(
            "Review comments",
            pr.review_comments,
            "info",
            "Number of review discussions. Very high counts may indicate quality concerns.",
        ),
        _metric(
            "Requested changes",
            pr.requested_changes,
            "warn" if pr.requested_changes else "ok",
            "Times reviewers requested changes. High → use smaller PRs and seek earlier feedback.",
        ),
        _metric(
            "Commits after review",
            pr.commits_after_review,
            "warn" if pr.commits_after_review > 3 else "ok",
            "Commits pushed after the first review (churn). Lower is better.",
        ),
        _metric(
            "Reverts detected",
            pr.reverts_detected,
            "bad" if pr.reverts_detected else "ok",
            "Commits whose message mentions 'revert'. Investigate the root cause.",
        ),
    ]


def _build_pr_analyses(report: EpicReport) -> dict[str, dict]:
    risk_by_key = {_pr_key(r.repository, r.number): r for r in report.pr_risks}
    analyses: dict[str, dict] = {}
    for pr in report.all_pull_requests:
        key = _pr_key(pr.repository, pr.number)
        risk = risk_by_key.get(key)
        q = pr.code_quality
        analyses[key] = {
            "number": pr.number,
            "title": pr.title,
            "repository": pr.repository,
            "author": pr.author,
            "status": pr.status,
            "url": pr.url,
            "branch": pr.branch,
            "additions": pr.additions,
            "deletions": pr.deletions,
            "changed_files": pr.changed_files,
            "commits": pr.commits,
            "time_to_merge_hours": pr.time_to_merge_hours,
            "risk": None
            if risk is None
            else {
                "score": risk.score,
                "level": risk.level,
                "components": [
                    {"name": c.name.replace("_", " "), "contribution": c.contribution}
                    for c in risk.components
                ],
            },
            "quality": None
            if q is None
            else {
                "cyclomatic_proxy": q.branch_keywords_added,
                "cognitive_proxy": q.nesting_score,
                "code_smells": q.code_smells,
                "debug_statements": q.debug_statements,
                "todos": q.todos_added,
                "long_lines": q.long_lines,
                "has_tests": q.has_tests,
            },
            "notes": q.notes if q else ["No diff available to evaluate."],
            "quality_metrics": _quality_metrics(pr),
            "rework_metrics": _rework_metrics(pr),
        }
    return analyses


def render_html(report: EpicReport) -> str:
    env = _build_env()
    template = env.get_template("dashboard.html")
    return template.render(
        report=report,
        epic=report.epic,
        charts=charts.build_all(report),
        risk_levels={r.number: r.level for r in report.pr_risks},
        story_risk_levels={r.key: r for r in report.story_risks},
        pr_data_json=json.dumps(_build_pr_analyses(report)),
        pr_key=_pr_key,
    )


def write_html(report: EpicReport, path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_html(report), encoding="utf-8")
    return target
