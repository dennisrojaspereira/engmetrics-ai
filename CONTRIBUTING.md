# Contributing

Thanks for your interest in improving **EngMetrics AI**! This is a small, focused open source tool — contributions that keep it simple, well-tested, and well-documented are very welcome.

New to open source? Look for the [`good first issue`](https://github.com/engmetrics-ai/engmetrics-ai/labels/good%20first%20issue) label — these are explicitly scoped for first-time contributors.

---

## First contribution walkthrough

### 1. Fork and clone

```bash
# Fork via GitHub UI, then:
git clone https://github.com/<your-username>/engmetrics-ai.git
cd ai-engineering-metrics
```

### 2. Set up the development environment

**Option A — Python (recommended for code changes):**

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .\.venv\Scripts\Activate.ps1

pip install -e ".[dev]"
pre-commit install               # installs lint/format hooks
```

**Option B — Docker (no Python required):**

```bash
docker compose build
docker compose run --rm app pytest    # run tests
docker compose run --rm app ruff check .
```

### 3. Verify the setup

```bash
# Should print the CLI help
ai-engineering-metrics --help

# Should generate a demo dashboard with no credentials
ai-engineering-metrics analyze --mock
# Dashboard written to reports/DEMO-1/dashboard.html
```

### 4. Make your change

- **Bug fix or small improvement** — edit code, add or adjust tests, done.
- **New feature** — open an issue first to align on approach before writing code.
- **Documentation** — edit or create Markdown files in `docs/` or root. No tests needed.

### 5. Run the quality gate

```bash
pytest                      # all tests must pass
ruff check .                # no lint errors
ruff format --check .       # code must be formatted
mypy                        # type checks (non-blocking for docs-only changes)
```

### 6. Commit

Use conventional commit prefixes so the changelog stays readable:

```bash
git commit -m "fix: correct lead time calculation when epic spans DST change"
git commit -m "feat: add --format csv option"
git commit -m "docs: improve Docker quick-start section in README"
git commit -m "chore: bump ruff to 0.6"
```

### 7. Open a pull request

- Push your branch to your fork.
- Open a PR against `main` on `engmetrics-ai/engmetrics-ai`.
- Fill in the PR template — especially the quality gate checklist.
- Keep the PR small and focused: one fix or feature per PR.

---

## Project layout

The codebase is layered so the domain stays I/O-free and reusable:

```
src/ai_engineering_metrics/
  cli.py          thin Typer shell — no business logic
  config.py       Pydantic Settings (env vars / .env / user config YAML)
  service.py      AnalysisService — the single orchestration entry point
  domain/         pure, I/O-free models + calculations
  integrations/   Jira / GitHub (gh CLI) / quality clients behind Protocols
  reports/        Jinja2 + Plotly dashboard rendering
  mock/           synthetic data for --mock
  storage/        JSON (de)serialisation
tests/
```

**Key rule:** never call external services from `domain/`. The domain layer must stay pure and testable without network access.

See [docs/architecture.md](docs/architecture.md) for the full component map and data flow.

---

## Development workflow

| Task | Command |
|---|---|
| Run tests | `pytest` |
| Run a single test | `pytest tests/test_metrics.py -k "lead_time"` |
| Lint | `ruff check .` |
| Format | `ruff format .` |
| Type check | `mypy` |
| Security scan | `bandit -c pyproject.toml -r src` |
| Generate demo | `ai-engineering-metrics analyze --mock` |

Pre-commit hooks run `ruff` and `bandit` automatically on `git commit`. Install them with `pre-commit install`.

---

## Common gotchas

- **`gh auth login` is required for real GitHub runs.** The tool delegates all GitHub access to the `gh` CLI. Mock mode never needs it.
- **Never commit `.env`.** It is git-ignored. Use `cp .env.example .env` and fill it in locally.
- **Never commit reports from real data.** The `reports/` and `generated/` directories are git-ignored. Only `examples/demo-dashboard.html` (mock data) is safe to commit.
- **Python 3.12+ required.** The tool uses 3.12+ type syntax. Check with `python --version`.

---

## Ground rules

- **Never commit secrets.** No `.env`, tokens, API keys, or real Jira/GitHub data.
- **Never log tokens or secrets** at any log level.
- Sample output committed to the repo must be generated in **mock mode** and contain no real org/URL/user data.
- Be respectful and constructive. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
- For security issues, do **not** open a public issue — see [SECURITY.md](SECURITY.md).

---

## Reporting bugs / requesting features

Open a [GitHub issue](https://github.com/engmetrics-ai/engmetrics-ai/issues) using the right template:

- **Bug report** — include the exact command, the error output (redacted), and your Python + OS version.
- **Feature request** — describe the use case and why existing behavior doesn't cover it.
- **Documentation improvement** — link to the file and section; a draft fix is welcome.

For open-ended discussions, use [GitHub Discussions](https://github.com/engmetrics-ai/engmetrics-ai/discussions) instead of issues.

---

## Need help?

- Read [docs/community.md](docs/community.md) for communication norms and expected response times.
- Look at existing merged PRs to see what a good contribution looks like.
- Open an issue or discussion if you are unsure about scope before writing code.
