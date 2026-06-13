# Summary

<!-- What does this PR change, and why? -->

## Quality gate

- [ ] Tests added or updated for the change
- [ ] `pytest` passes locally
- [ ] `ruff check .` and `ruff format --check .` pass
- [ ] `mypy` passes
- [ ] Mock mode still works (`ai-engineering-metrics analyze --epic DEMO-1 --mock`)

## Safety & hygiene

- [ ] No secrets committed (`.env`, tokens, API keys)
- [ ] No generated reports committed (`reports/`, `generated/` stay ignored)
- [ ] Any sample output committed is from **mock mode** only (no real data)
- [ ] README / docs updated if behavior or usage changed
- [ ] Security impact considered (new inputs, external calls, secret handling)

## Notes for reviewers

<!-- Screenshots (mock data only), trade-offs, follow-ups, etc. -->
