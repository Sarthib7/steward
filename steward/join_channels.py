from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)


async def list_public_channels(token: str, client: httpx.AsyncClient | None = None) -> list[dict]:
    own = client is None
    client = client or httpx.AsyncClient(timeout=30.0)
    channels: list[dict] = []
    cursor = None
    try:
        while True:
            params: dict[str, Any] = {"exclude_archived": True, "types": "public_channel", "limit": 200}
            if cursor:
                params["cursor"] = cursor
            r = await client.get(
                "https://slack.com/api/conversations.list",
                headers={"Authorization": f"Bearer {token}"},
                params=params,
            )
            data = r.json()
            if not data.get("ok"):
                log.warning("conversations.list failed: %s", data.get("error"))
                return channels
            channels.extend(data.get("channels") or [])
            cursor = (data.get("response_metadata") or {}).get("next_cursor") or None
            if not cursor:
                break
        return channels
    finally:
        if own:
            await client.aclose()


async def join_public_channels(token: str, client: httpx.AsyncClient | None = None) -> int:
    own = client is None
    client = client or httpx.AsyncClient(timeout=30.0)
    joined = 0
    try:
        channels = await list_public_channels(token, client=client)
        for ch in channels:
            if ch.get("is_archived"):
                continue
            if ch.get("is_member"):
                continue
            r = await client.post(
                "https://slack.com/api/conversations.join",
                headers={"Authorization": f"Bearer {token}"},
                data={"channel": ch["id"]},
            )
            data = r.json()
            if data.get("ok"):
                joined += 1
            elif data.get("error") == "ratelimited":
                await asyncio.sleep(float(r.headers.get("Retry-After", "5")))
            else:
                log.warning("join %s failed: %s", ch.get("id"), data.get("error"))
        return joined
    finally:
        if own:
            await client.aclose()


async def channel_id_for_name(
    name: str,
    token: str,
    client: httpx.AsyncClient | None = None,
) -> str | None:
    name = (name or "").lstrip("#")
    if not name:
        return None
    channels = await list_public_channels(token, client=client)
    for ch in channels:
        if ch.get("name") == name:
            return ch.get("id")
    return None


async def join_channel_ids(
    token: str,
    channel_ids: list[str],
    client: httpx.AsyncClient | None = None,
) -> dict[str, str]:
    own = client is None
    client = client or httpx.AsyncClient(timeout=30.0)
    results: dict[str, str] = {}
    try:
        for cid in channel_ids:
            if not cid:
                continue
            r = await client.post(
                "https://slack.com/api/conversations.join",
                headers={"Authorization": f"Bearer {token}"},
                data={"channel": cid},
            )
            data = r.json()
            if data.get("ok") or data.get("error") == "already_in_channel":
                results[cid] = "ok"
            elif data.get("error") == "ratelimited":
                await asyncio.sleep(float(r.headers.get("Retry-After", "5")))
                results[cid] = "ratelimited"
            else:
                err = str(data.get("error") or "unknown")
                results[cid] = err
                log.warning("join %s failed: %s", cid, err)
        return results
    finally:
        if own:
            await client.aclose()
