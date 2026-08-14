from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from steward.join_channels import join_channel_ids, join_public_channels
from steward.allowlist import is_allowed


@pytest.mark.asyncio
async def test_join_skips_archived():
    client = AsyncMock()
    list_resp = MagicMock()
    list_resp.json.return_value = {
        "ok": True,
        "channels": [
            {"id": "C1", "is_archived": False, "is_member": False},
            {"id": "C2", "is_archived": True, "is_member": False},
            {"id": "C3", "is_archived": False, "is_member": True},
        ],
        "response_metadata": {},
    }
    join_resp = MagicMock()
    join_resp.json.return_value = {"ok": True}
    join_resp.headers = {}
    client.get = AsyncMock(return_value=list_resp)
    client.post = AsyncMock(return_value=join_resp)
    n = await join_public_channels("xoxb", client=client)
    assert n == 1
    client.post.assert_awaited_once()


def test_digest_channel_gate():
    assert is_allowed("C1", ["C1"]) is True
    assert is_allowed("C9", ["C1"]) is False


@pytest.mark.asyncio
async def test_join_channel_ids_ok_already_and_error():
    client = AsyncMock()
    ok = MagicMock()
    ok.json.return_value = {"ok": True}
    ok.headers = {}
    already = MagicMock()
    already.json.return_value = {"ok": False, "error": "already_in_channel"}
    already.headers = {}
    denied = MagicMock()
    denied.json.return_value = {"ok": False, "error": "method_not_supported_for_channel_type"}
    denied.headers = {}
    client.post = AsyncMock(side_effect=[ok, already, denied])
    out = await join_channel_ids("xoxb", ["C1", "C2", "C3"], client=client)
    assert out == {
        "C1": "ok",
        "C2": "ok",
        "C3": "method_not_supported_for_channel_type",
    }
    assert client.post.await_count == 3
