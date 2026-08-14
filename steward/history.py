from __future__ import annotations

from typing import Any

import httpx

from steward.events import should_ingest_message


async def fetch_channel_history(
    token: str,
    channel_id: str,
    client: httpx.AsyncClient | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    own = client is None
    client = client or httpx.AsyncClient(timeout=30.0)
    try:
        r = await client.get(
            "https://slack.com/api/conversations.history",
            headers={"Authorization": f"Bearer {token}"},
            params={"channel": channel_id, "limit": limit},
        )
        data = r.json()
        if not data.get("ok"):
            return {"error": str(data.get("error") or "unknown"), "messages": []}
        return {"error": None, "messages": data.get("messages") or []}
    finally:
        if own:
            await client.aclose()


def messages_to_ingest(
    raw: list[dict],
    channel: str,
    bot_user_id: str = "",
) -> list[dict]:
    items: list[dict] = []
    for m in raw:
        event = {
            "type": "message",
            "channel": channel,
            "user": m.get("user"),
            "text": m.get("text") or "",
            "ts": m.get("ts"),
            "subtype": m.get("subtype"),
            "bot_id": m.get("bot_id"),
        }
        if should_ingest_message(event, bot_user_id):
            items.append({"event": event})
    return items
