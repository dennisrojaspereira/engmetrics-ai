# engmetrics.ai — Engineering Intelligence Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Status: Experimental](https://img.shields.io/badge/status-experimental-orange.svg)](#status)

**An Engineering Intelligence Platform for Tech Leads and Engineering Managers — unifying Jira, GitHub and AI usage data into actionable delivery insights.**

> ⚠️ **Status: experimental.** This is an early open-source experiment, not a
> production-ready product. Metrics are heuristic, integrations are still
> evolving, and APIs may change. Use it to *start a conversation* about delivery
> health — not as a system of record. See [Status](#status).

> 📊 **Live example:** open [`examples/demo-dashboard.html`](examples/demo-dashboard.html)
> in your browser — a full dashboard generated in mock mode (100% synthetic data).

> 📄 **Product Vision:** see [`docs/product-vision.md`](docs/product-vision.md) for the
> full platform vision, target audience and roadmap.

---

## The problem

Tech Leads and Engineering Managers are accountable for delivery outcomes they
rarely have a unified view of. The data exists — but it is scattered:

- **Jira** holds stories, estimates and status — but no code signal.
- **GitHub** holds PRs, reviews and merge times — but no delivery context.
- **AI tools** track token consumption — but not what it produced.

The questions that matter go unanswered every sprint:

- How long does a feature take from first commit to production? (Lead Time)
- How often are we actually deploying? (Deployment Frequency)
- What fraction of deploys cause incidents — and how fast do we recover?
- Are we actually shipping faster with AI, or just spending tokens?
- Where is review churn signalling scope creep or unclear requirements?
- Which epics carried the highest rework cost — and why?

Nobody has time to stitch this together manually.

## Why this project exists

**engmetrics.ai** connects Jira and GitHub into a single engineering intelligence
view — scoped to an epic, rendered as an interactive dashboard. It's built to be:

- **Honest** — it shows what the data supports and clearly marks what's missing.
- **Explainable** — every score and metric breaks down into named, inspectable
  factors. No black-box numbers.
- **Local & private** — runs on your machine, talks to your APIs, writes a local
  HTML file. No server, no data leaves your environment.
- **Evolvable** — a clean domain/integration/report split so it can grow into a
  web app, an AI agent or a CI step without a rewrite.

## Who it's for

**Primary:** Tech Leads and Engineering Managers who need a weekly pulse on
delivery health — flow efficiency, quality signals, deployment frequency and
rework costs — without building their own dashboards.

**Secondary:** Staff Engineers, Architects and CTOs who need a system-level view
across epics, teams or quarters.

The platform is useful to any engineering team, regardless of AI tool adoption.
AI metrics are one of five intelligence lenses, not a prerequisite.

---

## Engineering Intelligence Copilot

The long-term vision for engmetrics.ai goes beyond a dashboard you remember to
open. The goal is an **Engineering Intelligence Copilot** — a system that
surfaces the right insight at the right moment, embedded in how Tech Leads and
EMs already work.

**What this means in practice:**

- **Proactive signals, not reactive queries.** The copilot detects anomalies —
  a spike in change failure rate, a lead time regression, an epic with
  unusually high rework — before the sprint review.
- **Natural language over dashboards.** Ask: *"Which epics this quarter had the
  highest rework cost?"* or *"How does our deployment frequency compare to last
  quarter?"* and get a direct, cited answer.
- **Integrated into existing workflows.** Insights delivered where the team
  already communicates: PR comments, Slack digests, Jira comments, GitHub
  Actions summaries.
- **Agent-composable.** The clean domain model and JSON output are designed to
  be consumed by AI agents. An LLM can receive the `EpicReport` JSON and
  produce a narrative delivery review or a risk assessment with no bespoke
  integration.

The current CLI and HTML dashboard are the **foundation** of this copilot —
the data pipeline and domain model that make the intelligence possible.

---

## Platform capabilities

### Data sources

Jira and GitHub are the only required data sources. No new instrumentation.

- **Jira** — epics, stories, story points, estimates, resolution dates and
  custom fields (AI tokens, hours with/without AI).
- **GitHub (via `gh` CLI)** — PRs matched to Jira keys by title/branch,
  enriched with diff stats and review data. Repo auto-detected from git remote.

### Five intelligence lenses

| Lens | What it measures |
|------|-----------------|
| **DORA metrics** | Deployment Frequency, Lead Time, Change Failure Rate, MTTR — with Elite/High/Medium/Low bands |
| **AI impact** | Hours saved, token consumption per story point / per hour saved, estimated cost, AI Dependency Risk Score |
| **Code quality** | Per-PR diff heuristics: complexity proxies, code smells, debug statements, test coverage |
| **Flow & rework** | Time to merge, review cycles, requested changes, commits after review, reverts |
| **Risk intelligence** | Explainable 0–100 risk score blending token intensity, coverage, complexity and review churn |

All five lenses are available for any team on Jira + GitHub. AI impact requires
AI token data in Jira — but the other four lenses work without it.

### Dashboard features

- **Epic → dashboard in one command.** Point it at a Jira epic key; get an HTML
  dashboard (or JSON).
- **Per-PR evaluation popup** — click any PR to see its quality/rework
  breakdown, improvement tooltips, a risk score and a link to GitHub.
- **Mock mode** — a full, realistic demo with zero credentials.
- **JSON output** — for piping into agents or other tools.

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
git clone https://github.com/engmetrics-ai/engmetrics-ai.git
cd ai-engineering-metrics

python -m venv .venv
source .venv/bin/activate                # Windows: .\.venv\Scripts\Activate.ps1

pip install -e ".[dev]"                  # add ",pandas" for optional aggregations
```

## Quick start

```bash
# 1) Try it with zero setup (no epic, no credentials needed):
ai-engineering-metrics analyze --mock

# 2) Configure real access:
cp .env.example .env        # fill in Jira values
gh auth login               # authenticate GitHub

# 3) Analyze a real epic (GitHub repo auto-detected from the current git remote):
cd /path/to/your/repo
ai-engineering-metrics analyze --epic PROJ-123 --open
```

Each run writes a self-contained bundle named after the epic:

```text
reports/
└── DEMO-1/
    ├── dashboard.html      # the interactive dashboard (open this)
    ├── metrics.json        # full machine-readable report
    ├── stories.csv         # one row per story
    └── pull_requests.csv   # one row per PR
```

## Example commands

```bash
# Zero-setup demo (epic defaults to DEMO-1)
ai-engineering-metrics analyze --mock

# Real epic -> reports/PROJ-123/ ; --open launches the dashboard
ai-engineering-metrics analyze -e PROJ-123 --open

# Choose where the bundle goes
ai-engineering-metrics analyze -e PROJ-123 -o ./out

# Only one artifact (all | html | json | csv)
ai-engineering-metrics analyze -e PROJ-123 --format csv

# Pipe the metrics JSON to another tool
ai-engineering-metrics analyze -e PROJ-123 --stdout | jq .ai_usage

# Point at a specific GitHub repo (overrides .env and auto-detection)
ai-engineering-metrics analyze -e PROJ-123 --repo your-org/your-repo

# Backward-compatible single-file output
ai-engineering-metrics analyze -e PROJ-123 -o ./reports/PROJ-123.html
```

> `python -m ai_engineering_metrics analyze ...` works identically to the
> `ai-engineering-metrics` console script.

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

Each run creates a per-epic bundle (`<output>/<EPIC>/`) containing
`dashboard.html`, `metrics.json`, `stories.csv` and `pull_requests.csv`.

| Directory | Committed? | Contents |
|---|---|---|
| `examples/` | ✅ yes | Sanitized demo dashboard (mock data only). |
| `reports/`  | ❌ git-ignored | Bundles from **real** data — may contain private info. |
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

See [`docs/product-vision.md`](docs/product-vision.md) for the full evolution
path. Near-term priorities:

- [ ] Multi-epic / portfolio rollups and trends over time.
- [ ] Real static-analysis quality source (SonarQube/CodeClimate).
- [ ] Pluggable AI-cost providers and per-model token pricing.
- [ ] First-class review metrics via richer GitHub data (no simulation needed).
- [ ] Publish to PyPI; optional web UI.
- [ ] Agent-ready JSON API for LLM narrative reports (copilot foundation).

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
[CHANGELOG.md](CHANGELOG.md) · [Product Vision](docs/product-vision.md) ·
[ADR-001](docs/adr/ADR-001-platform-repositioning.md)
