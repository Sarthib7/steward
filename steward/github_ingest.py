from __future__ import annotations

import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)


def parse_repos(repos: list[str]) -> list[tuple[str, str]]:
    out = []
    for r in repos:
        owner, name = r.split("/", 1)
        out.append((owner, name))
    return out


def map_issue_to_memory(item: dict[str, Any], repo: str) -> dict[str, Any]:
    kind = "pull_request" if "pull_request" in item else "issue"
    html_url = item["html_url"]
    login = (item.get("user") or {}).get("login")
    updated = item.get("updated_at")
    title = item.get("title")
    state = item.get("state")
    number = item.get("number")
    text = (
        f"[GitHub Memory] repo={repo} kind={kind} number={number} state={state} "
        f"login={login} updated_at={updated} html_url={html_url}\n{title}"
    )
    meta = {
        "html_url": html_url,
        "number": number,
        "title": title,
        "state": state,
        "login": login,
        "updated_at": updated,
        "repo": repo,
    }
    row = {
        "origin": "github",
        "channel_id": None,
        "repo": repo,
        "permalink": html_url,
        "text": f"{kind} #{number}: {title}",
        "occurred_at": updated,
        "updated_at": updated,
        "state": state,
        "user_id": None,
        "kind": kind,
    }
    return {"text": text, "metadata": meta, "ledger_row": row}


async def fetch_repo_issues(
    owner: str,
    repo: str,
    since: str,
    token: str | None = None,
    client: httpx.AsyncClient | None = None,
) -> list[dict]:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    params = {
        "state": "all",
        "sort": "updated",
        "direction": "desc",
        "since": since,
        "per_page": 100,
    }
    own = client is None
    client = client or httpx.AsyncClient(timeout=30.0)
    try:
        r = await client.get(url, headers=headers, params=params)
        if r.status_code in (401, 403, 404):
            log.warning("github skip %s/%s status=%s", owner, repo, r.status_code)
            return []
        r.raise_for_status()
        items = r.json()
        if len(items) >= 100:
            log.warning("github cap 100 items for %s/%s", owner, repo)
        return items
    except httpx.HTTPError as e:
        log.warning("github error %s/%s: %s", owner, repo, e)
        return []
    finally:
        if own:
            await client.aclose()
