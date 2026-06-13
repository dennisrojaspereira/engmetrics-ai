"""Plotly chart builders.

Each function returns a self-contained ``<div>`` (Plotly.js is loaded once from
CDN by the template) so the dashboard can drop them straight into the layout.
The palette is the executive purple/white theme used across the dashboard.
"""

from __future__ import annotations

from collections import defaultdict

import plotly.graph_objects as go

from ai_engineering_metrics.domain.models import EpicReport

PURPLE = "#6d28d9"
PURPLE_LIGHT = "#a78bfa"
PURPLE_DARK = "#4c1d95"
GREEN = "#10b981"
AMBER = "#f59e0b"
RED = "#ef4444"
GRID = "#ede9fe"
FONT = "Inter, Segoe UI, system-ui, sans-serif"

_LEVEL_COLOR = {
    "low": GREEN,
    "moderate": AMBER,
    "high": "#fb7185",
    "critical": RED,
    "unknown": PURPLE_LIGHT,
}

_LAYOUT = dict(
    paper_bgcolor="white",
    plot_bgcolor="white",
    font=dict(family=FONT, color="#3b3b52", size=13),
    margin=dict(l=20, r=20, t=30, b=40),
    height=320,
    xaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
    yaxis=dict(gridcolor=GRID, zerolinecolor=GRID),
)


def _to_div(fig: go.Figure, div_id: str) -> str:
    fig.update_layout(**_LAYOUT)
    return fig.to_html(
        full_html=False, include_plotlyjs=False, div_id=div_id, config={"displayModeBar": False}
    )


def tokens_per_story(report: EpicReport) -> str:
    keys = [s.key for s in report.stories]
    tokens = [s.ai_tokens for s in report.stories]
    fig = go.Figure(go.Bar(x=keys, y=tokens, marker_color=PURPLE))
    fig.update_layout(yaxis_title="AI tokens")
    return _to_div(fig, "chart-tokens-story")


def tokens_per_dev(report: EpicReport) -> str:
    agg: dict[str, int] = defaultdict(int)
    for s in report.stories:
        agg[s.assignee or "Unassigned"] += s.ai_tokens
    devs = list(agg.keys())
    tokens = list(agg.values())
    fig = go.Figure(go.Bar(x=devs, y=tokens, marker_color=PURPLE_LIGHT))
    fig.update_layout(yaxis_title="AI tokens")
    return _to_div(fig, "chart-tokens-dev")


def savings_per_story(report: EpicReport) -> str:
    keys = [s.key for s in report.stories]
    without = [s.estimate_without_ai_hours for s in report.stories]
    with_ai = [s.estimate_with_ai_hours for s in report.stories]
    fig = go.Figure()
    fig.add_bar(name="Without AI", x=keys, y=without, marker_color=PURPLE_DARK)
    fig.add_bar(name="With AI", x=keys, y=with_ai, marker_color=GREEN)
    fig.update_layout(barmode="group", yaxis_title="Estimated hours", legend=dict(orientation="h"))
    return _to_div(fig, "chart-savings-story")


def tokens_per_changed_line(report: EpicReport) -> str:
    keys: list[str] = []
    ratios: list[float] = []
    for s in report.stories:
        changed = s.total_changed_lines
        if changed:
            keys.append(s.key)
            ratios.append(round(s.ai_tokens / changed, 1))

    # Fallback: when PRs are linked to the epic (not individual stories), there
    # is no per-story changed-line data — show the epic-level aggregate instead.
    if not keys:
        total_changed = sum(pr.total_changed_lines for pr in report.all_pull_requests)
        if total_changed:
            keys = [f"{report.epic.key} (all PRs)"]
            ratios = [report.ai_usage.tokens_per_changed_line]

    fig = go.Figure(go.Bar(x=keys, y=ratios, marker_color=PURPLE))
    fig.update_layout(yaxis_title="Tokens / changed line")
    return _to_div(fig, "chart-tokens-line")


def risk_per_pr(report: EpicReport) -> str:
    labels = [f"#{r.number}" for r in report.pr_risks]
    scores = [r.score for r in report.pr_risks]
    colors = [_LEVEL_COLOR.get(r.level, PURPLE) for r in report.pr_risks]
    fig = go.Figure(go.Bar(x=labels, y=scores, marker_color=colors))
    fig.update_layout(yaxis_title="Risk score", yaxis=dict(range=[0, 100], gridcolor=GRID))
    return _to_div(fig, "chart-risk-pr")


def build_all(report: EpicReport) -> dict[str, str]:
    return {
        "tokens_per_story": tokens_per_story(report),
        "tokens_per_dev": tokens_per_dev(report),
        "savings_per_story": savings_per_story(report),
        "tokens_per_changed_line": tokens_per_changed_line(report),
        "risk_per_pr": risk_per_pr(report),
    }
