# Security testing strategy

This project runs automated security checks on every pull request (see
`.github/workflows/security.yml`).

## What runs today

| Layer | Tool | Where |
|-------|------|-------|
| **SAST** (static analysis) | [Bandit](https://bandit.readthedocs.io) | `security.yml` + pre-commit + `make security` |
| **Dependency audit** | [pip-audit](https://pypi.org/project/pip-audit/) | `security.yml` + `make audit` |
| **Secret scanning** | [gitleaks](https://github.com/gitleaks/gitleaks) | `security.yml` + pre-commit + `make secrets` |
| Lint / type safety | ruff, mypy | `ci.yml` + pre-commit |

Bandit is configured in `pyproject.toml` (`[tool.bandit]`). We intentionally use
`subprocess` with an argument **list** (never `shell=True`) and resolve the
executable via `shutil.which`, so the generic subprocess warnings (`B404`,
`B603`) are skipped — there is no shell-injection surface.

## DAST — evaluation

**Decision: deferred (documented as future work).**

DAST (Dynamic Application Security Testing) targets *running web applications*.
This project is:

- a **local CLI**, and
- a generator of a **static, self-contained HTML file**.

There is no server, no authentication surface, no request handling and no
user-supplied input rendered for other users — so classic DAST (active scanning,
fuzzing endpoints) has very little to bite on. Forcing it in now would be
over-engineering.

### If/when DAST becomes worthwhile

The one meaningful surface is the **generated dashboard HTML** (it embeds data
from Jira/GitHub via Jinja2, which auto-escapes, plus Plotly from a CDN). A
lightweight, proportionate check would be an **OWASP ZAP baseline scan against
the sanitized mock dashboard** served locally — passive only, no auth:

```yaml
# Sketch for a future .github/workflows/dast.yml (NOT enabled yet)
# - generate the mock dashboard:
#     ai-engineering-metrics analyze --epic DEMO-1 --mock --output ./generated/demo.html
# - serve it:  python -m http.server 8000 --directory generated &
# - scan it:
#     uses: zaproxy/action-baseline@v0.12.0
#     with:
#       target: "http://localhost:8000/demo.html"
# Only ever scan mock output — never a report built from real data.
```

This is tracked on the roadmap and can be added once the dashboard grows
interactive/server-side features. Until then, the SAST + dependency + secret
gates above are the right level of coverage.
