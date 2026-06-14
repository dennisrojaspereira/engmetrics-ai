# Release Process

This document describes how to cut a new release of EngMetrics AI. It is intended for maintainers.

---

## Versioning

EngMetrics AI follows [Semantic Versioning](https://semver.org/):

| Increment | When |
|---|---|
| **PATCH** (0.1.**x**) | Bug fixes; no new features; backward-compatible |
| **MINOR** (0.**x**.0) | New backward-compatible features |
| **MAJOR** (**x**.0.0) | Breaking changes to CLI flags, config, or output format |

---

## Step-by-step release checklist

### 1. Confirm `main` is green

```bash
git checkout main && git pull origin main
pytest
ruff check .
mypy
```

All checks must pass before starting the release.

### 2. Update the version in `pyproject.toml`

```toml
[project]
version = "0.2.0"   # bump this
```

### 3. Update `CHANGELOG.md`

Move items from `[Unreleased]` to the new version section and add the release date:

```markdown
## [0.2.0] - 2026-07-01

### Added
- …

### Fixed
- …

## [Unreleased]

[Unreleased]: https://github.com/engmetrics-ai/engmetrics-ai/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/engmetrics-ai/engmetrics-ai/compare/v0.1.0...v0.2.0
```

Keep the `[Unreleased]` section empty and ready for the next cycle.

### 4. Commit the release

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release v0.2.0"
```

### 5. Tag the release

```bash
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin main --tags
```

### 6. Create a GitHub Release

```bash
gh release create v0.2.0 \
  --title "v0.2.0" \
  --notes "$(awk '/^## \[0\.2\.0\]/,/^## \[/' CHANGELOG.md | head -n -1)"
```

Or use the GitHub UI: go to **Releases → Draft a new release**, select the tag, paste the CHANGELOG section.

### 7. Publish to PyPI (when configured)

```bash
python -m build
twine upload dist/*
```

> PyPI publishing is not yet set up. This step is a placeholder for when it is. See [ROADMAP.md](../ROADMAP.md).

### 8. Regenerate and commit the demo dashboard

If the dashboard template or mock data changed:

```bash
ai-engineering-metrics analyze --epic DEMO-1 --mock --output examples/demo-dashboard.html
git add examples/demo-dashboard.html
git commit -m "chore: regenerate demo dashboard for v0.2.0"
git push origin main
```

---

## Hotfix releases

For urgent bug fixes on an already-released version:

```bash
git checkout -b hotfix/v0.1.1 v0.1.0
# apply the fix
git commit -m "fix: <description>"
# bump version in pyproject.toml to 0.1.1
# update CHANGELOG
git tag -a v0.1.1 -m "Hotfix v0.1.1"
git push origin hotfix/v0.1.1 --tags
gh release create v0.1.1 --title "v0.1.1 (hotfix)" --notes "..."
# merge back to main if needed
```

---

## Release cadence

There is no fixed release schedule. Releases are cut when:

- A meaningful feature set has accumulated in `[Unreleased]`, **or**
- A bug fix needs to be published urgently (hotfix).

Minor releases should not contain too many unrelated changes — keep them focused so that the CHANGELOG is readable and the diff is reviewable.
