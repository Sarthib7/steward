from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from steward.github_ingest import fetch_repo_issues, map_issue_to_memory, parse_repos


def test_parse_repos_default():
    assert parse_repos(["topoteretes/cognee", "qdrant/qdrant"]) == [
        ("topoteretes", "cognee"),
        ("qdrant", "qdrant"),
    ]


def test_map_issue_vs_pr():
    issue = {
        "html_url": "https://github.com/topoteretes/cognee/issues/1",
        "number": 1,
        "title": "docs",
        "state": "open",
        "updated_at": "2026-08-14T10:00:00Z",
        "user": {"login": "alice"},
    }
    pr = {**issue, "html_url": "https://github.com/topoteretes/cognee/pull/2", "number": 2, "pull_request": {}}
    mi = map_issue_to_memory(issue, "topoteretes/cognee")
    mp = map_issue_to_memory(pr, "topoteretes/cognee")
    assert mi["ledger_row"]["kind"] == "issue"
    assert mp["ledger_row"]["kind"] == "pull_request"
    assert mi["ledger_row"]["permalink"].startswith("https://github.com/")
    assert "api.github.com" not in mi["ledger_row"]["permalink"]


@pytest.mark.asyncio
async def test_fetch_403_returns_empty():
    client = AsyncMock()
    resp = MagicMock()
    resp.status_code = 403
    resp.headers = {}
    client.get = AsyncMock(return_value=resp)
    items = await fetch_repo_issues("o", "r", "2026-01-01T00:00:00Z", client=client)
    assert items == []
