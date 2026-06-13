# Screenshots

Drop dashboard screenshots here. The main [README](../../README.md) references
these exact filenames:

| File | What to capture |
|------|-----------------|
| `dashboard-overview.png` | Top of the dashboard: epic header + KPI cards + a chart or two. |
| `pr-popup.png` | The per-PR evaluation popup (Code quality + Rework + risk breakdown + tooltip). |

## How to capture (sanitized)

Use **mock mode** so the screenshots contain no real company data:

```bash
python -m ai_engineering_metrics analyze --epic DEMO-1 --mock --output ./generated/demo.html
```

1. Open `generated/demo.html` in your browser.
2. For `dashboard-overview.png`: screenshot the header + cards + charts area.
3. For `pr-popup.png`: click a PR row to open the popup, then screenshot it.
4. Save the PNGs in this folder with the names above.

## Guidelines

- **Only screenshot mock-mode output** — never a dashboard generated from real
  Jira/GitHub data (it can leak URLs, issue keys, author and repo names).
- Prefer a light background and a width around 1200–1600px.
- Keep file sizes reasonable (PNG, optimized).
