import asyncio
import hashlib
import hmac
import time
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


def _env(monkeypatch, tmp_path):
    monkeypatch.setenv("STEWARD_SKIP_STARTUP", "1")
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "sig")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("STEWARD_ALLOWLIST_CHANNELS", "C1")
    monkeypatch.setenv("STEWARD_DIGEST_CHANNEL", "C1")
    monkeypatch.setenv("LLM_API_KEY", "or-key")
    monkeypatch.setenv("VECTOR_DB_URL", "https://example.qdrant.io")
    monkeypatch.setenv("VECTOR_DB_KEY", "q-key")
    monkeypatch.setenv("STEWARD_LEDGER", str(tmp_path / "ingest.jsonl"))


def _sig(secret: str, ts: str, body: bytes) -> str:
    base = b"v0:" + ts.encode() + b":" + body
    digest = hmac.new(secret.encode(), base, hashlib.sha256).hexdigest()
    return f"v0={digest}"


def _headers(body: bytes) -> dict:
    ts = str(int(time.time()))
    return {
        "X-Slack-Request-Timestamp": ts,
        "X-Slack-Signature": _sig("sig", ts, body),
        "Content-Type": "application/x-www-form-urlencoded",
    }


@pytest.fixture
def client(monkeypatch, tmp_path):
    _env(monkeypatch, tmp_path)
    # Reset cached settings
    import steward.app as appmod

    appmod.settings = None
    # Point ledger at tmp
    from steward.config import load_settings

    s = load_settings()
    object.__setattr__(s, "ledger_path", str(tmp_path / "ingest.jsonl")) if False else None
    # frozen dataclass — patch get_settings
    s2 = load_settings()
    from dataclasses import replace

    s2 = replace(s2, ledger_path=str(tmp_path / "ingest.jsonl"))
    monkeypatch.setattr(appmod, "get_settings", lambda: s2)
    monkeypatch.setattr(appmod, "settings", s2)
    with TestClient(appmod.app) as c:
        yield c, s2, tmp_path


def test_url_verification(client):
    c, _, _ = client
    r = c.post(
        "/api/v1/slack/events",
        json={"type": "url_verification", "challenge": "abc123"},
    )
    assert r.status_code == 200
    assert r.text == "abc123"


def test_invalid_signature_401(client):
    c, _, _ = client
    body = b"command=%2Fsteward-ask&text=hi&channel_id=C1&response_url=https%3A%2F%2Fexample.com"
    r = c.post(
        "/api/v1/slack/commands",
        content=body,
        headers={
            "X-Slack-Request-Timestamp": str(int(time.time())),
            "X-Slack-Signature": "v0=deadbeef",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    assert r.status_code == 401


def test_off_allowlist_refuse(client):
    c, _, _ = client
    body = b"command=%2Fsteward-ask&text=hi&channel_id=C9&user_id=U1&response_url=https%3A%2F%2Fexample.com"
    r = c.post("/api/v1/slack/commands", content=body, headers=_headers(body))
    assert r.status_code == 200
    assert "isn't enabled" in r.json()["text"]


def test_remember_calls_memory(client):
    c, s, tmp_path = client
    with (
        patch("steward.app.remember_text", new_callable=AsyncMock) as rem,
        patch("steward.app._post_response_url", new_callable=AsyncMock),
    ):
        body = (
            b"command=%2Fsteward-remember&text=vectors%20on%20qdrant&channel_id=C1"
            b"&user_id=U1&response_url=https%3A%2F%2Fexample.com"
        )
        r = c.post("/api/v1/slack/commands", content=body, headers=_headers(body))
        assert r.status_code == 200
        _wait_awaited(rem)
        rem.assert_awaited()
        from steward.ledger import read_rows

        rows = read_rows(s.ledger_path)
        assert any(row.get("origin") == "remember" for row in rows)


def test_digest_bad_arg(client):
    c, _, _ = client
    body = b"command=%2Fsteward-digest&text=nope&channel_id=C1&user_id=U1&response_url=https%3A%2F%2Fexample.com"
    r = c.post("/api/v1/slack/commands", content=body, headers=_headers(body))
    assert r.status_code == 200
    assert "Usage" in r.json()["text"]


def _wait_awaited(mock, timeout=2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if mock.await_count:
            return
        time.sleep(0.02)
    raise AssertionError("background mock not awaited")


def test_ask_returns_before_slow_recall(client):
    c, _, _ = client

    async def slow_recall(*_a, **_k):
        await asyncio.sleep(3)
        return []

    with (
        patch("steward.app.recall", side_effect=slow_recall),
        patch("steward.app._post_response_url", new_callable=AsyncMock),
    ):
        body = (
            b"command=%2Fsteward-ask&text=where%20are%20vectors%20stored"
            b"&channel_id=C1&user_id=U1&response_url=https%3A%2F%2Fexample.com"
        )
        t0 = time.perf_counter()
        r = c.post("/api/v1/slack/commands", content=body, headers=_headers(body))
        elapsed = time.perf_counter() - t0
        assert r.status_code == 200
        assert elapsed < 1.0


def test_ask_on_allowlist_calls_recall(client):
    c, _, _ = client
    with (
        patch("steward.app.recall", new_callable=AsyncMock, return_value=[
            {"origin": "remember", "text": "vectors live on Qdrant Cloud", "permalink": "cmd"}
        ]) as rec,
        patch("steward.app._post_response_url", new_callable=AsyncMock) as post,
    ):
        body = (
            b"command=%2Fsteward-ask&text=where%20are%20vectors%20stored"
            b"&channel_id=C1&user_id=U1&response_url=https%3A%2F%2Fexample.com"
        )
        r = c.post("/api/v1/slack/commands", content=body, headers=_headers(body))
        assert r.status_code == 200
        _wait_awaited(rec)
        rec.assert_awaited()
        _wait_awaited(post)
        assert post.await_count >= 1


def test_ingest_only_channel_slash_still_refused(client, monkeypatch):
    c, s, _ = client
    from dataclasses import replace
    import steward.app as appmod

    s3 = replace(s, ingest_channels=["C9"])
    monkeypatch.setattr(appmod, "get_settings", lambda: s3)
    body = b"command=%2Fsteward-ask&text=hi&channel_id=C9&user_id=U1&response_url=https%3A%2F%2Fexample.com"
    r = c.post("/api/v1/slack/commands", content=body, headers=_headers(body))
    assert r.status_code == 200
    assert "isn't enabled" in r.json()["text"]


def test_ask_cites_ingest_channel_memory(client, monkeypatch):
    c, s, _ = client
    from dataclasses import replace
    import steward.app as appmod

    s3 = replace(s, ingest_channels=["C9"])
    monkeypatch.setattr(appmod, "get_settings", lambda: s3)
    with (
        patch("steward.app.recall", new_callable=AsyncMock, return_value=[
            {
                "origin": "slack_channel",
                "channel_id": "C9",
                "text": "vectors live on Qdrant Cloud",
                "permalink": "p9",
            }
        ]),
        patch("steward.app._post_response_url", new_callable=AsyncMock) as post,
    ):
        body = (
            b"command=%2Fsteward-ask&text=where%20are%20vectors%20stored"
            b"&channel_id=C1&user_id=U1&response_url=https%3A%2F%2Fexample.com"
        )
        r = c.post("/api/v1/slack/commands", content=body, headers=_headers(body))
        assert r.status_code == 200
        _wait_awaited(post)
        posted = " ".join(str(call.args) for call in post.await_args_list)
        assert "SOURCED" in posted
        assert "Qdrant Cloud" in posted
