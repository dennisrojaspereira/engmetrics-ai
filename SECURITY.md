# Security Policy

## Reporting a vulnerability

If you discover a security issue, please **do not open a public issue**.
Instead, report it privately via
[GitHub Security Advisories](https://github.com/engmetrics-ai/engmetrics-ai/security/advisories/new)
(Security → Report a vulnerability).

Please include steps to reproduce and the affected version. We aim to
acknowledge reports within a few business days.

## Handling of secrets

This tool talks to JIRA and GitHub. It is designed to keep credentials out of
source control and out of logs:

- **JIRA** credentials (`JIRA_BASE_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`) are
  read from environment variables / a local `.env` file that is **git-ignored**.
- **GitHub** access uses the official `gh` CLI (`gh auth login`); the tool
  never stores or reads a GitHub token directly.
- Secrets are marked non-`repr` in the config models and are **never logged**.
  HTTP error handling deliberately avoids echoing response bodies that could
  contain tokens.

## If you cloned/forked this repo

- Copy `.env.example` to `.env` and fill in your own values. **Never commit
  `.env`.**
- Reports generated from real data live in `reports/` and `generated/`, which
  are git-ignored. Do not commit them — they may contain JIRA URLs, issue keys,
  author names and repository names.
- Only the sanitized `examples/demo-dashboard.html` (mock data) is safe to
  share publicly.

## Rotating a leaked token

If a JIRA API token is ever exposed (e.g. pasted into a chat, commit, or log),
revoke it immediately at
<https://id.atlassian.com/manage-profile/security/api-tokens> and issue a new
one.
