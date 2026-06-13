# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-06-13

First public release.

### Added
- CLI (`ai-engineering-metrics analyze`) that turns a JIRA epic into an
  executive HTML dashboard or a JSON report.
- JIRA integration: resolves the epic and its stories, reads custom fields
  (AI tokens, story points) and derives "hours saved" from story points when
  no estimate fields exist.
- GitHub integration via the `gh` CLI: discovers pull requests by issue key in
  title/branch (with literal-key verification to avoid fuzzy false positives),
  enriches them with diff/review data, and auto-detects the repo from the
  current git remote.
- Metrics: productivity, AI-usage (tokens & cost), rework, per-PR diff-based
  code-quality heuristics, and an explainable 0–100 AI Dependency Risk Score.
- Dashboard: KPI cards, charts (Plotly), epic-level Code quality & Rework
  overviews, and a per-PR evaluation popup with improvement tooltips and a link
  to the PR.
- Mock mode (`--mock`) with realistic synthetic data; JSON output (`--format json`).
- Optional demo simulation files for story points and PR review/rework signals.

[Unreleased]: https://github.com/dennisrojaspereira/ai-engineering-metrics/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/dennisrojaspereira/ai-engineering-metrics/releases/tag/v0.1.0
