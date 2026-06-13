"""Unit tests for the gh-CLI-backed GitHub client.

These never invoke `gh`: the auth check and the JSON-returning command runner are
patched so we can assert on the parsing/aggregation logic alone.
"""

from ai_engineering_metrics.config import GitHubConfig
from ai_engineering_metrics.integrations.github_client import GitHubClient, _mentions_key


def test_mentions_key_rejects_fuzzy_matches():
    # "KAN-5" must not match a PR that only contains "KAN-4" and a stray "5".
    assert _mentions_key("upgrade TypeScript to 5.8.x [KAN-4]", "KAN-5") is False
    assert _mentions_key("feat/KAN-4-upgrade", "KAN-40") is False
    assert _mentions_key("fix login [KAN-5]", "KAN-5") is True
    assert _mentions_key("branch feat/kan-5-thing", "KAN-5") is True


_PR_VIEW = {
    "number": 1421,
    "title": "KAN-20002 Tokenise card vault",
    "author": {"login": "anamuller"},
    "headRefName": "feature/KAN-20002-card-vault",
    "state": "MERGED",
    "createdAt": "2026-05-03T09:00:00Z",
    "mergedAt": "2026-05-05T14:00:00Z",
    "additions": 940,
    "deletions": 210,
    "changedFiles": 18,
    "commits": [
        {"committedDate": "2026-05-03T10:00:00Z", "messageHeadline": "init", "messageBody": ""},
        {
            "committedDate": "2026-05-04T12:00:00Z",
            "messageHeadline": "address review",
            "messageBody": "",
        },
        {
            "committedDate": "2026-05-04T13:00:00Z",
            "messageHeadline": "Revert bad change",
            "messageBody": "",
        },
    ],
    "reviews": [
        {
            "author": {"login": "liu-wei"},
            "state": "CHANGES_REQUESTED",
            "submittedAt": "2026-05-04T09:00:00Z",
            "body": "please fix",
        },
        {
            "author": {"login": "pedro-souza"},
            "state": "APPROVED",
            "submittedAt": "2026-05-05T08:00:00Z",
            "body": "",
        },
    ],
}


def _client(monkeypatch) -> GitHubClient:
    monkeypatch.setattr(GitHubClient, "_ensure_gh_ready", lambda self: None)
    client = GitHubClient(GitHubConfig(org="acme"))
    # Keep tests hermetic: never shell out to `gh` for the (optional) diff.
    monkeypatch.setattr(client, "_run_text", lambda args: "")
    return client


def test_load_pull_request_parses_gh_json(monkeypatch):
    client = _client(monkeypatch)
    monkeypatch.setattr(client, "_run_json", lambda args: _PR_VIEW)

    pr = client._load_pull_request("acme/payments-api", 1421, "KAN-20002")

    assert pr is not None
    assert pr.number == 1421
    assert pr.author == "anamuller"
    assert pr.status == "merged"
    assert pr.additions == 940 and pr.deletions == 210
    assert pr.total_changed_lines == 1150
    assert pr.commits == 3
    assert pr.requested_changes == 1
    assert pr.review_cycles == 2  # one CHANGES_REQUESTED + one APPROVED
    assert pr.reviewers == ["liu-wei", "pedro-souza"]
    assert pr.review_comments == 1  # only the non-empty review body
    assert pr.commits_after_review == 2  # two commits after the first review
    assert pr.reverts_detected == 1
    assert pr.time_to_merge_hours == 53.0


def test_find_pull_requests_dedupes_search_and_branch(monkeypatch):
    client = _client(monkeypatch)

    def fake_run_json(args):
        if args[0] == "search":
            return [{"number": 1421, "repository": {"nameWithOwner": "acme/payments-api"}}]
        if args[:2] == ["pr", "list"]:
            return [{"number": 1421, "headRefName": "feature/KAN-20002-card-vault"}]
        return _PR_VIEW

    monkeypatch.setattr(client, "_run_json", fake_run_json)
    # Force the branch-search path by scoping to an explicit repo.
    client._config = GitHubConfig(org="acme", repositories=["payments-api"], search_all_repos=False)

    prs = client.find_pull_requests("KAN-20002")
    assert len(prs) == 1  # same PR found by search + branch must be deduped
    assert prs[0].number == 1421
