# Product Vision — engmetrics.ai

> **Engineering Intelligence Platform for Tech Leads and Engineering Managers**

---

## Vision Statement

engmetrics.ai gives Tech Leads and Engineering Managers a single, honest view of
their team's delivery health — by connecting the data that already exists in Jira
and GitHub into actionable engineering intelligence.

No new processes. No extra tooling. Just clarity.

---

## The Problem Space

Engineering Managers and Tech Leads are accountable for outcomes they can rarely
measure directly. The data they need is scattered across at least three systems:

| System | What it holds | What's missing |
|--------|---------------|----------------|
| Jira | Stories, epics, estimates, status | No code signal |
| GitHub | PRs, reviews, diff size, merge time | No delivery context |
| AI tools | Token consumption, sessions | No impact measurement |

Today, most teams answer "how are we doing?" with a sprint velocity number and a
gut feeling. That's not enough to lead well.

The questions that matter — and that go unanswered — are:

- How often are we actually deploying to production? (Deployment Frequency)
- How long does a feature take from first commit to production? (Lead Time)
- What fraction of our deploys cause an incident? (Change Failure Rate)
- When we break production, how fast do we recover? (MTTR)
- Is AI assistance making us faster, or just adding cost and complexity?
- Where is review churn signaling scope creep or unclear requirements?
- Which epics have the highest rework cost — and why?

These are not vanity metrics. They are the operational signals that determine
whether a team compounds value or compounds technical and organisational debt.

---

## Target Audience

### Primary: Tech Leads and Engineering Managers

People responsible for the delivery health of one or more squads. They need:

- A weekly pulse on flow efficiency (lead time, deployment frequency)
- An honest signal on quality (coverage, churn, rework)
- Data to justify investment decisions to leadership
- Early warning on velocity decay or dependency risks

They do not have time to build their own dashboards. They should not have to.

### Secondary: Staff Engineers and Architects

People who own cross-cutting concerns — tech debt strategy, platform reliability,
AI tool adoption. They need a system view that spans multiple teams or epics.

### Tertiary: VPs of Engineering and CTOs

Leadership that needs portfolio-level signals: DORA performance bands, AI ROI at
scale, consistency of delivery across teams.

---

## Platform Capabilities

engmetrics.ai surfaces engineering intelligence across five lenses. All five are
derived from the same two data sources: Jira and GitHub.

### 1. DORA Metrics

The industry-standard DevOps Research and Assessment metrics, scoped to an epic
or team:

- **Deployment Frequency** — how often code reaches production
- **Lead Time for Changes** — from first commit to production deployment
- **Change Failure Rate** — fraction of deployments that cause incidents
- **Mean Time to Restore (MTTR)** — recovery speed after a failure

Performance bands (Elite / High / Medium / Low) align with the DORA State of
DevOps report, giving teams a benchmark against the industry.

### 2. AI Impact Metrics

A unique capability: quantifying the ROI of AI coding tools at the story and epic
level:

- Hours saved vs. baseline estimates
- AI token consumption per story point, per hour saved, per changed line
- Estimated AI cost vs. delivery value
- AI Dependency Risk Score — an 8-factor indicator of over-reliance

AI metrics are one platform capability, not the whole product. A team with no AI
tooling still gets full value from lenses 1, 3, 4 and 5.

### 3. Code Quality Signals

Per-PR heuristics derived from diffs (no static-analysis integration needed):
complexity proxies, code smells, debug statements, test coverage signals.
Aggregated to an epic overview for pattern recognition across a delivery cycle.

### 4. Flow & Rework

The friction in the delivery process:
- Time to merge
- Review cycles, review comments, requested changes
- Commits pushed after review (churn indicator)
- Reverts detected

High rework is not just slow — it is a signal that requirements, technical
design or team alignment broke down somewhere upstream.

### 5. Risk Intelligence

The AI Dependency Risk Score (0–100) blends token intensity, savings rate, test
coverage, complexity, review churn and static signals into a single, explainable
number. Each component is visible and nameable — no black-box risk scores.

---

## Data Sources: Jira and GitHub

Jira and GitHub are the primary and only required data sources. They are already
where engineering teams do their work — no new instrumentation is needed.

**From Jira:**
- Epics, stories, story points, status and assignees
- Custom fields: AI token consumption, hour estimates with/without AI
- Issue resolution dates (for lead time)

**From GitHub (via the `gh` CLI):**
- Pull requests matched to Jira issue keys by title and branch name
- Diff stats: additions, deletions, files changed
- Review data: cycles, comments, requested changes, approvers
- Merge timestamps (for time-to-merge and lead time)

This two-source architecture is intentional. It covers the full delivery loop —
from intent (Jira) to execution (GitHub) — without requiring access to
deployment pipelines, monitoring systems or third-party integrations in the
initial version.

Future data sources (GitHub Actions for deployment events, SonarQube/CodeClimate
for static analysis, PagerDuty for incident data) extend the platform without
replacing its core.

---

## Engineering Intelligence Copilot

The long-term vision for engmetrics.ai is not a dashboard you remember to open.
It is a **copilot** that surfaces the right insight at the right moment —
embedded in the workflow of a Tech Lead or EM.

What this means in practice:

**Proactive signals, not reactive queries.**
Rather than requiring an EM to run a report, the copilot detects anomalies —
a sudden spike in change failure rate, a lead time regression, an epic with
unusually high rework — and surfaces them before the sprint review.

**Natural language over dashboards.**
An EM should be able to ask: *"Which epics this quarter had the highest rework
cost?"* or *"How does our deployment frequency compare to last quarter?"* and
get a direct, cited answer — not a pivot table.

**Integrated into existing workflows.**
Insights delivered where the team already communicates: pull request comments,
Slack/Teams digests, Jira comments, or GitHub Actions summaries — not in a
separate tool that competes for attention.

**Agent-composable.**
The clean domain model and JSON output of engmetrics.ai are designed to be
consumed by AI agents. An LLM can receive the `EpicReport` JSON and produce
a narrative delivery review, a risk assessment or a team retrospective brief
— without any bespoke integration.

The current CLI and HTML dashboard are the **foundation** of this copilot —
the data pipeline and domain model that make the intelligence possible.

---

## Business Value

For a team of 8 engineers:

| Value driver | Mechanism |
|---|---|
| **Faster incident response** | MTTR visibility surfaces slow recovery patterns early |
| **Reduced rework cost** | Review churn signals catch scope creep at the PR level |
| **AI ROI accountability** | Token consumption per hour saved justifies (or questions) AI tooling spend |
| **Delivery predictability** | Lead time trends make sprint commitments more credible |
| **Risk-aware shipping** | AI Dependency Risk Score flags coverage gaps before they reach production |

Engineering Managers currently spend significant time in Jira and GitHub trying
to form the picture that engmetrics.ai assembles automatically. The platform
turns that manual synthesis into a structured, reproducible and shareable
artefact.

---

## What This Is Not

- Not an employee monitoring tool. All metrics are team and epic-level, not
  individual performance ratings.
- Not a replacement for engineering judgment. Numbers inform — they do not
  decide.
- Not an AI-only tool. The platform is useful to any team, regardless of AI
  tool adoption.
- Not a system of record. It is a signal and a conversation starter. Source of
  truth remains in Jira and GitHub.

---

## Evolution Path

| Phase | Scope | Status |
|-------|-------|--------|
| **v0.1 — AI Impact CLI** | Single epic, AI metrics + rework + quality, HTML dashboard | Shipped |
| **v0.2 — DORA + Deployments** | DORA metrics, deployment timeline, per-deploy lead time | Shipped |
| **v0.3 — Platform positioning** | Product vision, ADR, README reframe | This PR |
| **v0.4 — Multi-epic rollups** | Portfolio view, trend over time, team-level aggregation | Planned |
| **v0.5 — Static analysis** | SonarQube / CodeClimate integration, real coverage data | Planned |
| **v1.0 — Copilot foundation** | Agent-ready JSON API, LLM narrative reports, CI step | Roadmap |

---

*Last updated: 2026-06-14*
