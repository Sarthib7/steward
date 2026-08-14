from unittest.mock import AsyncMock, MagicMock

import pytest

from steward.history import fetch_channel_history, messages_to_ingest


@pytest.mark.asyncio
async def test_fetch_history_missing_scope():
    client = AsyncMock()
    resp = MagicMock()
    resp.json.return_value = {"ok": False, "error": "missing_scope"}
    resp.headers = {}
    client.get = AsyncMock(return_value=resp)
    out = await fetch_channel_history("xoxb", "C0BP8V9S0UC", client=client)
    assert out["error"] == "missing_scope"
    assert out["messages"] == []


def test_messages_to_ingest_skips_bots_and_empty():
    channel = "C0BP8V9S0UC"
    raw = [
        {"user": "U1", "text": "demo at 9", "ts": "1723600000.000100"},
        {"subtype": "bot_message", "text": "bot", "ts": "1723600001.000100"},
        {"bot_id": "B1", "text": "also bot", "ts": "1723600002.000100"},
        {"user": "U2", "text": "  ", "ts": "1723600003.000100"},
        {"user": "UBOT", "text": "self", "ts": "1723600004.000100"},
    ]
    items = messages_to_ingest(raw, channel, bot_user_id="UBOT")
    assert len(items) == 1
    assert items[0]["event"]["text"] == "demo at 9"
    assert items[0]["event"]["channel"] == channel
