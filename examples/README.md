# Examples

This folder contains **sanitized, committable** sample output.

- [`demo-dashboard.html`](demo-dashboard.html) — a full dashboard generated in
  **mock mode** (`--mock`). All data is synthetic (fictional org `acme`,
  fictional people and issues). It contains **no real credentials, JIRA URLs,
  usernames or repository names**, so it is safe to commit and share.

Regenerate it any time with:

```bash
python -m ai_engineering_metrics analyze --epic DEMO-1 --mock --output ./examples/demo-dashboard.html
```

## Output directories — what goes where

| Directory | Committed? | Purpose |
|-----------|------------|---------|
| `examples/` | ✅ yes (sanitized) | Demo output safe to share publicly. |
| `reports/`  | ❌ no (git-ignored) | Reports you generate from **real** JIRA/GitHub data. May contain private info. |
| `generated/`| ❌ no (git-ignored) | Scratch / throwaway machine output. |

Only `reports/.gitkeep` and `generated/.gitkeep` are tracked so the directories
exist on a fresh clone. Never commit a report produced from real data — it can
leak JIRA URLs, issue keys, author names and repository names.
