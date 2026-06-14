# ADR-001: Reposition engmetrics.ai as an Engineering Intelligence Platform

| Field | Value |
|-------|-------|
| **Status** | Accepted |
| **Date** | 2026-06-14 |
| **Deciders** | Dennis Rojas Pereira |
| **Related docs** | [Product Vision](../product-vision.md), [README](../../README.md) |

---

## Context

engmetrics.ai launched (v0.1) as **"AI Engineering Metrics"** — a CLI tool that
measures the impact of AI coding tools on a single Jira epic. The product
already integrates Jira and GitHub as data sources and produces metrics across
five lenses: productivity, AI usage & cost, code quality, rework, and an
AI Dependency Risk Score.

During early validation, two patterns emerged:

**1. The AI-specific framing is too narrow.**
Prospective users — Tech Leads and Engineering Managers — respond more strongly
to delivery intelligence questions (lead time, deployment frequency, rework
costs) than to AI-specific questions alone. Many teams have little or no AI
tool usage tracked in Jira, which means the current framing immediately excludes
them.

**2. The data model already supports a broader platform.**
Jira (stories, estimates, resolution dates) and GitHub (PRs, diffs, reviews,
merge times) together cover the full delivery loop. DORA metrics were added in
v0.2 from the same two data sources. The domain model — `EpicReport`,
`DoraMetrics`, `QualityMetrics`, `ReworkMetrics`, `RiskScore` — is already a
multi-capability engineering intelligence schema.

The product is doing more than AI metrics. The name, tagline and README do not
reflect that.

---

## Decision

We reposition engmetrics.ai as an **Engineering Intelligence Platform for Tech
Leads and Engineering Managers**, with the following changes:

1. **README** is updated to lead with the broader EM/TL value proposition and
   platform framing, while preserving all technical documentation unchanged.

2. **A Product Vision document** (`docs/product-vision.md`) is added, defining
   target audience, platform capabilities, data sources, the Engineering
   Intelligence Copilot concept, and the evolution path.

3. **AI metrics are preserved** as a first-class platform capability — they are
   not deprecated, renamed or reduced. They become "AI Impact" — one of five
   lenses alongside DORA, Code Quality, Flow & Rework, and Risk Intelligence.

4. **No code changes** are made in this PR. The repositioning is a documentation
   and product framing decision only. Technical implementation follows the new
   framing incrementally.

5. **The package name** (`ai-engineering-metrics`) and CLI command
   (`ai-engineering-metrics`) are not changed in this PR. A rename is a separate
   decision with package publication and backward-compatibility implications.

---

## Rationale

### Why "Engineering Intelligence Platform"?

The term covers what the tool actually does: it aggregates structured data from
engineering systems (Jira, GitHub) and converts it into actionable delivery
intelligence. "Metrics" suggests a static reporting tool; "intelligence" implies
analysis, pattern detection and actionable insight.

### Why "for Tech Leads and Engineering Managers"?

These are the people who (a) have the authority to act on the insights, (b) lack
a unified view today, and (c) are already paying the cost of not having one
through manual Jira/GitHub synthesis. Naming them explicitly in the positioning
reduces the cognitive work of evaluating the tool.

### Why keep AI metrics?

They are a differentiator, not a liability. No competing tool surfaces AI token
consumption per story point or per hour saved. The AI Dependency Risk Score is
unique. Framing them as one of five lenses — rather than the whole product —
makes the platform more broadly adoptable while retaining the differentiated
capability for teams that have invested in AI tooling.

### Why Jira + GitHub as the primary data sources?

They are where engineering work already lives. No new instrumentation means no
adoption barrier. The two-source model covers the full delivery loop:
intent (Jira) → execution (GitHub). Future integrations (deployment pipelines,
monitoring, incident management) extend the platform without replacing its core.

### Why introduce the Engineering Intelligence Copilot concept?

The copilot framing articulates the long-term direction: proactive, workflow-
integrated, agent-composable intelligence — rather than a dashboard that must be
remembered and opened. Naming it now aligns future technical decisions (API
design, JSON schema, LLM integration) toward a coherent destination.

---

## Consequences

### Positive

- The product is immediately relevant to teams with no AI tool tracking, not
  just those with Jira AI token fields.
- The DORA metrics addition (v0.2) is now a natural fit rather than a surprise
  feature addition.
- The product vision and ADR give contributors and stakeholders a shared
  reference for prioritisation decisions.
- The copilot framing creates a coherent narrative for the v1.0 roadmap.

### Negative / Risks

- **SEO / discoverability:** The existing `ai-engineering-metrics` name and
  "AI metrics" framing may have indexed positively. A gradual shift risks losing
  that signal before the new positioning builds its own.
  *Mitigation:* keep the package name and CLI command unchanged in this PR.

- **Expectation gap:** "Platform" implies more than a CLI tool. Some users may
  arrive expecting a web application.
  *Mitigation:* the README and product vision explicitly describe the current
  state (CLI, HTML dashboard) and distinguish it from the roadmap.

- **Scope creep risk:** A broader platform framing could invite feature requests
  that dilute focus.
  *Mitigation:* the "What This Is Not" section in the product vision document
  sets explicit scope boundaries.

---

## Related Decisions

- **ADR-002 (future):** Package rename from `ai-engineering-metrics` to a name
  that reflects the platform positioning (e.g. `engmetrics`).
- **ADR-003 (future):** Web API / agent interface design for the copilot
  foundation.
