# Contributing

Thanks for your interest in improving **ai-engineering-metrics**! This is a
small, focused tool — contributions that keep it simple and well-tested are very
welcome.

## Getting started

```bash
git clone https://github.com/dennisrojaspereira/ai-engineering-metrics.git
cd ai-engineering-metrics

python -m venv .venv
source .venv/bin/activate        # Windows: .\.venv\Scripts\Activate.ps1

pip install -e ".[dev]"
cp .env.example .env             # optional; only needed for real JIRA/GitHub runs
```

Run the tool with no external services using mock mode:

```bash
python -m ai_engineering_metrics analyze --epic DEMO-1 --mock --output ./generated/demo.html
```

## Project layout

The codebase is layered so the domain stays I/O-free and reusable:

```
domain/        pure models + metric/risk calculations (no I/O)
integrations/  JIRA / GitHub (gh CLI) / quality clients behind small Protocols
reports/       Jinja2 + Plotly dashboard rendering
service.py     orchestration (the single entry point)
cli.py         thin Typer shell
mock/          synthetic data for --mock
```

Keep new code in the matching layer; don't call external services from `domain/`.

## Development workflow

- **Tests:** `pytest` — please add/adjust tests for any change in behavior.
- **Lint/format:** `ruff check .` and `ruff format .`.
- **Conventional-ish commits** are appreciated (`feat:`, `fix:`, `docs:`, ...).
- Keep PRs small and focused; describe what changed and why.

## Ground rules

- **Never commit secrets.** `.env`, real reports (`reports/`, `generated/`),
  caches and editor state are git-ignored — keep it that way.
- **Never log tokens or secrets.**
- Sample output committed to the repo must be generated in **mock mode** and
  contain no real org/URL/user data (see `examples/`).
- Be respectful and constructive. By participating you agree to uphold a
  welcoming, harassment-free environment.

## Reporting bugs / requesting features

Open a GitHub issue with clear reproduction steps or a concrete use case.
For security issues, see [SECURITY.md](SECURITY.md) instead.
