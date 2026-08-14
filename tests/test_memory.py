import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import steward.memory as mem


@pytest.mark.asyncio
async def test_remember_calls_cognee_without_session_id():
    mock_cognee = MagicMock()
    mock_cognee.remember = AsyncMock(return_value=None)
    with (
        patch("steward.memory._cognee", mock_cognee),
        patch("steward.memory.ensure_qdrant_adapter"),
    ):
        await mem.remember_text("hello", dataset_name="steward", external_metadata={"permalink": "p"})
        kwargs = mock_cognee.remember.await_args.kwargs
        assert kwargs.get("dataset_name") == "steward"
        assert "session_id" not in kwargs


@pytest.mark.asyncio
async def test_recall_top_k_default():
    mock_cognee = MagicMock()
    mock_cognee.recall = AsyncMock(return_value=[{"text": "x"}])
    with (
        patch("steward.memory._cognee", mock_cognee),
        patch("steward.memory.ensure_qdrant_adapter"),
    ):
        hits = await mem.recall("q", datasets=["steward"])
        assert hits == [{"text": "x"}]
        assert mock_cognee.recall.await_args.kwargs.get("top_k") == 5


def test_ensure_qdrant_adapter_calls_register(monkeypatch):
    monkeypatch.delenv("STEWARD_SKIP_STARTUP", raising=False)
    mem._adapter_registered = False
    fake = MagicMock()
    fake.register = MagicMock()
    with patch.dict(sys.modules, {"cognee_community_vector_adapter_qdrant": fake}):
        mem.ensure_qdrant_adapter()
    fake.register.assert_called_once()
    assert mem._adapter_registered is True
    mem._adapter_registered = False


def test_ensure_qdrant_adapter_skips_when_startup_skipped(monkeypatch):
    monkeypatch.setenv("STEWARD_SKIP_STARTUP", "1")
    mem._adapter_registered = False
    fake = MagicMock()
    with patch.dict(sys.modules, {"cognee_community_vector_adapter_qdrant": fake}):
        mem.ensure_qdrant_adapter()
    fake.register.assert_not_called()
    assert mem._adapter_registered is False
