# AI Engineering Metrics

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Status: Experimental](https://img.shields.io/badge/status-experimental-orange.svg)](#status)

**Measure the real impact of AI on your engineering delivery — by connecting Jira epics, GitHub pull requests and AI token consumption into one dashboard.**

> ⚠️ **Status: experimental.** This is an early open-source experiment, not a
> production-ready product. Metrics are heuristic, integrations are still
> evolving, and APIs may change. Use it to *start a conversation* about AI
> impact — not as a system of record. See [Status](#status).

> 📊 **Live example:** open [`examples/demo-dashboard.html`](examples/demo-dashboard.html)
> in your browser — a full dashboard generated in mock mode (100% synthetic data).

---

## The problem

Teams are adopting AI coding tools fast, but most can't answer basic questions:

- Are we actually shipping faster with AI, or just spending tokens?
- How much does the AI assistance for an epic *cost* — and what did it save?
- Is AI-assisted code creating more rework (review cycles, churn, reverts)?
- Where is our delivery becoming *dependent* on AI without a quality safety net?

The data to answer this already exists — scattered across Jira (estimates, story
points, AI token fields), GitHub (PR size, reviews, merge times) and your AI
billing. Nobody has time to stitch it together.

## Why this project exists

**AI Engineering Metrics** stitches that data together for a single Jira **epic**
and renders an executive-style dashboard. It's built to be:

- **Honest** — it shows what the data supports and clearly marks what's missing.
- **Explainable** — every risk score and metric breaks down into named factors.
- **Local & private** — runs on your machine, talks to your APIs, writes a local
  HTML file. No server, no data leaves your environment.
- **Evolvable** — a clean domain/integration/report split so it can grow into a
  web app, an agent or a CI step without a rewrite.

## Who it's for

Tech Leads · Staff Engineers · Engineering Managers · CTOs · and any developer
trying to quantify how AI is changing how their team ships.

---

## Features

- **Epic → dashboard in one command.** Point it at a Jira epic key; get an HTML
  dashboard (or JSON).
- **Jira integration** — resolves the epic, its stories and custom fields (AI
  tokens, story points). Derives *hours saved* from story points when no
  estimate fields exist.
- **GitHub integration via the `gh` CLI** — discovers PRs by issue key in the
  title/branch (with literal-key matching to avoid false positives), enriches
  them with diff and review data, and **auto-detects the repo** from your git
  remote.
- **Metrics across five lenses:**
  - *Productivity* — hours saved, % savings, lead time, PRs per story.
  - *AI usage & cost* — tokens per story / PR / changed line / story point /
    hour saved, plus estimated cost.
  - *Code quality* — per-PR heuristics from the diff (complexity proxies, code
    smells, debug statements, tests touched), aggregated to an epic overview.
  - *Rework* — time to merge, review cycles, requested changes, commits after
    review, reverts.
  - *AI Dependency Risk Score (0–100)* — an explainable, weighted blend of token
    intensity, low savings, low coverage, complexity and review churn.
- **Per-PR evaluation popup** — click any PR to see its quality/rework breakdown,
  improvement tooltips, a risk breakdown and a link to the PR on GitHub.
- **Mock mode** — a full, realistic demo with zero credentials.
- **JSON output** — for piping into other tools.

## Mock mode

Mock mode runs the entire pipeline against realistic **synthetic** data (1 epic,
5 stories, 8 PRs, quality + AI-usage metrics) — no Jira, no GitHub, no tokens:

```bash
python -m ai_engineering_metrics analyze --epic DEMO-1 --mock --output ./generated/demo.html
```

It's the fastest way to see what the tool produces, and it's what generates the
committed [`examples/demo-dashboard.html`](examples/demo-dashboard.html).

---

## Installation

**Requirements:** Python **3.12+**, and the [GitHub CLI](https://cli.github.com)
(`gh`) authenticated once with `gh auth login` (used for all GitHub access — no
`GITHUB_TOKEN` needed).

### As a tool

```bash
pipx install ai-engineering-metrics      # isolated, on your PATH
# or run without installing:
uvx ai-engineering-metrics --help
```

> Not yet published to PyPI — for now install from a local checkout:
> `pipx install .` (or `uvx --from . ai-engineering-metrics`).

### From source (development)

```bash
git clone https://github.com/dennisrojaspereira/ai-engineering-metrics.git
cd ai-engineering-metrics

python -m venv .venv
source .venv/bin/activate                # Windows: .\.venv\Scripts\Activate.ps1

pip install -e ".[dev]"                  # add ",pandas" for optional aggregations
```

## Quick start

```bash
# 1) Try it with no setup at all:
python -m ai_engineering_metrics analyze --epic DEMO-1 --mock --output ./generated/demo.html

# 2) Configure real access:
cp .env.example .env        # fill in Jira values
gh auth login               # authenticate GitHub

# 3) Analyze a real epic (GitHub repo auto-detected from the current git remote):
cd /path/to/your/repo
ai-engineering-metrics analyze --epic PROJ-123
```

## Example commands

```bash
# HTML dashboard to a specific path
python -m ai_engineering_metrics analyze --epic PROJ-123 --output ./reports/PROJ-123.html

# JSON to stdout (pipeable)
python -m ai_engineering_metrics analyze --epic PROJ-123 --format json

# Point at a specific GitHub repo (overrides .env and auto-detection)
ai-engineering-metrics analyze --epic PROJ-123 --repo your-org/your-repo

# Verbose logging
ai-engineering-metrics analyze --epic PROJ-123 --verbose
```

If `--output` is omitted, the report is written to `./reports/<EPIC>.<ext>`
(except `--format json` with no output, which prints to stdout).

---

## Jira configuration

The tool reads a Jira Cloud epic, its linked stories and selected custom fields.
You need a Jira API token (create one at
<https://id.atlassian.com/manage-profile/security/api-tokens>).

| Variable | Meaning |
|---|---|
| `JIRA_BASE_URL` | e.g. `https://your-company.atlassian.net` |
| `JIRA_EMAIL` | the account email for the API token |
| `JIRA_API_TOKEN` | your Jira API token (**keep secret**) |
| `JIRA_EPIC_LINK_FIELD` | epic-link custom field (company-managed projects) |
| `JIRA_AI_TOKENS_FIELD` | custom field holding AI tokens spent |
| `JIRA_ESTIMATE_WITHOUT_AI_FIELD` / `..._WITH_AI_FIELD` | estimate fields (hours), optional |
| `JIRA_STORY_POINTS_FIELD` | story-points field (e.g. `customfield_10016`) |

Find custom field ids at `GET /rest/api/3/field`. If your project has no story
points or estimate fields, see [Estimation](#environment-variables) — the tool
can derive *hours saved* from story points.

## GitHub configuration

GitHub access goes through the **`gh` CLI**, so there is no token to manage in
this tool — just run `gh auth login` once. The target repository is resolved in
this order:

1. `--repo owner/name` flag
2. `.env` (`GITHUB_ORG` / `GITHUB_REPOSITORIES`)
3. **auto-detected** from the current directory's git remote
4. fallback: Jira's development panel

PRs are matched to issues by the Jira key appearing in the PR title or branch
(e.g. `feat/PROJ-123-...` or `[PROJ-123]`).

## Environment variables

Copy [`.env.example`](.env.example) to `.env` and fill it in. **`.env` is
git-ignored — never commit it.**

| Variable | Default | Purpose |
|---|---|---|
| `MOCK_MODE` | `false` | Force mock data (same as `--mock`). |
| `JIRA_BASE_URL` / `JIRA_EMAIL` / `JIRA_API_TOKEN` | — | Jira Cloud auth. |
| `JIRA_*_FIELD` | see `.env.example` | Custom field ids. |
| `GITHUB_ORG` / `GITHUB_REPOSITORIES` | — | Optional; otherwise auto-detected. |
| `GITHUB_SEARCH_ALL_REPOS` | `true` | Search the whole org vs. listed repos. |
| `AI_TOKEN_PRICE_INPUT_PER_1M` / `..._OUTPUT_PER_1M` | `3.00` / `15.00` | Per-1M token prices. |
| `DEFAULT_TOKEN_PRICE_PER_1M` | `6.00` | Blended price for cost estimates. |
| `STORY_POINT_HOURS` | `1.0` | Hours per story point (without-AI baseline). |
| `AI_SAVINGS_PERCENT` | `40.0` | Assumed AI savings % when no estimate fields exist. |
| `QUALITY_METRICS_FILE` | — | Optional JSON of static-analysis metrics. |
| `PR_SIMULATION_FILE` | — | **Demo only:** simulate review/rework signals that can't be produced for real (e.g. self-review). Leave blank in real use. |

## Generated outputs

| Directory | Committed? | Contents |
|---|---|---|
| `examples/` | ✅ yes | Sanitized demo dashboard (mock data only). |
| `reports/`  | ❌ git-ignored | Reports from **real** data — may contain private info. |
| `generated/`| ❌ git-ignored | Scratch / throwaway output. |

Reports built from real data can contain Jira URLs, issue keys, author names and
repository names, so `reports/` and `generated/` are git-ignored by design.
**Never commit a real report.** Only `examples/demo-dashboard.html` (mock) is
safe to share. See [SECURITY.md](SECURITY.md).

## Screenshots

> _Placeholders — add real screenshots under `docs/screenshots/` before release._

| Overview & KPI cards | Per-PR evaluation popup |
|---|---|
| ![Dashboard overview](docs/screenshots/dashboard-overview.png) | ![PR evaluation popup](docs/screenshots/pr-popup.png) |

(Until then, open [`examples/demo-dashboard.html`](examples/demo-dashboard.html).)

---

## Architecture overview

```
src/ai_engineering_metrics/
  cli.py              # Typer CLI (thin shell)
  config.py           # Pydantic settings loaded from .env
  service.py          # AnalysisService — orchestration, the single entry point
  domain/             # pure, I/O-free models + calculations
    models.py         #   shared Pydantic models
    metrics.py        #   productivity / AI-usage / rework
    risk.py           #   AI Dependency Risk Score
  integrations/       # external systems behind small Protocols
    base.py           #   retry/rate-limit HTTP client + source protocols
    jira_client.py    #   Jira Cloud REST (search/jql + dev panel)
    github_client.py  #   GitHub via the gh CLI (PR discovery + enrichment)
    quality_client.py #   JSON / null quality sources
  reports/            # Jinja2 + Plotly dashboard rendering
  mock/               # synthetic data for --mock
  storage/            # JSON (de)serialisation
tests/
```

**Design principle:** the domain is pure and I/O-free; integrations sit behind
small `Protocol`s; `AnalysisService` is the one orchestration entry point. The
same core can back a future web API, agent or CI step — only a thin adapter is
needed.

## Roadmap

This is experimental and the roadmap is intentionally open. Likely next steps:

- [ ] Real static-analysis quality source (SonarQube/CodeClimate) instead of
      diff heuristics.
- [ ] Multi-epic / portfolio rollups and trends over time.
- [ ] Pluggable AI-cost providers and per-model token pricing.
- [ ] First-class review metrics (no simulation needed) via richer GitHub data.
- [ ] Publish to PyPI; optional web UI.
- [ ] Export to CSV / data warehouse.

Ideas and use cases are very welcome — open an issue.

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup,
project layout and workflow. Run the tests with `pytest` and lint with
`ruff check .`.

## Security

Secrets are read from environment variables / a git-ignored `.env`, GitHub auth
is delegated to the `gh` CLI, and tokens are never logged. Please report
vulnerabilities privately — see [SECURITY.md](SECURITY.md). If a token is ever
exposed, **rotate it immediately**.

## Status

**Experimental.** Expect rough edges, heuristic metrics and breaking changes.
It is **not** production-ready and makes no guarantees of accuracy. Treat its
numbers as directional signals to inform a conversation, not as ground truth.

## License

[MIT](LICENSE) © Dennis Rojas Pereira

See also: [CONTRIBUTING.md](CONTRIBUTING.md) · [SECURITY.md](SECURITY.md) ·
[CHANGELOG.md](CHANGELOG.md)
