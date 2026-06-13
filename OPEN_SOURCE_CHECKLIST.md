# Open Source Readiness Checklist

Status for the first public release of **ai-engineering-metrics**.

## Security
- [x] No secrets in tracked files (JIRA/GitHub tokens, API keys, passwords)
- [x] `.env` is git-ignored (and `.env.*` except `.env.example`)
- [x] Secrets are read from env vars only; never logged
- [x] GitHub access via `gh` CLI (no token stored by the tool)
- [x] No real generated reports tracked (`reports/`, `generated/` ignored)
- [x] No personal data in committed files (sample output is mock-only)
- [ ] **Action required:** rotate any JIRA API token that was used locally /
      pasted anywhere (see SECURITY.md)

## Repository hygiene
- [x] `.gitignore` blocks `.env`, `__pycache__/`, `.pytest_cache/`,
      `.ruff_cache/`, `.vscode/`, `.idea/`, `.claude/`, coverage, caches, temp
      files, local DBs, and generated reports
- [x] `.gitkeep` keeps `reports/` and `generated/` present without their contents
- [x] Editor/agent state (`.claude/`) ignored

## Documentation
- [x] `README.md` — overview, install (pip/pipx/uvx), configure, usage, metrics
- [x] `.env.example` with placeholders (no real values)
- [x] `CONTRIBUTING.md`
- [x] `SECURITY.md`
- [x] `CHANGELOG.md`
- [x] `LICENSE` (MIT)
- [x] Installation documented
- [x] Sample output documented (`examples/demo-dashboard.html`)

## Functionality
- [x] Mock mode works (`--mock`, no JIRA/GitHub needed)
- [x] Project runs locally (`python -m ai_engineering_metrics analyze ...`)
- [x] Tests passing (`pytest` — 15 passed)
- [x] JSON output works (`--format json`)

## Packaging
- [x] `pyproject.toml` with name, version, description, readme, license
- [x] Console entry point `ai-engineering-metrics`
- [x] Classifiers + project URLs
- [x] `requires-python = ">=3.12"`
- [x] Installable via `pip` / `pipx` / `uvx`
- [ ] Published to PyPI (intentionally **not** done yet)

## Pre-publish manual steps
- [ ] Review `git status` to confirm no ignored file is staged
- [ ] Set the GitHub repo description, topics and license display
- [ ] Create the first commit and tag `v0.1.0`
