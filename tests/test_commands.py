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
    appmod._seen_mentions.clear()
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
        assert r.json() == {"response_type": "ephemeral", "text": "Recalling…"}


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


def test_ask_digest_intent_skips_recall_and_posts_shell(client):
    c, s, _ = client
    from datetime import datetime, timezone

    from steward.ledger import append_row

    now = datetime.now(timezone.utc).isoformat()
    append_row(
        s.ledger_path,
        {
            "origin": "github",
            "channel_id": None,
            "repo": "qdrant/qdrant",
            "permalink": "https://github.com/qdrant/qdrant/issues/1",
            "text": "issue #1: payload index",
            "occurred_at": now,
            "updated_at": now,
            "state": "open",
            "user_id": None,
            "kind": "issue",
        },
    )
    with (
        patch("steward.app.recall", new_callable=AsyncMock) as rec,
        patch("steward.app._ingest_github_since", new_callable=AsyncMock, return_value=1),
        patch("steward.app.channel_id_for_name", new_callable=AsyncMock, return_value="C0BP8V9S0UC"),
        patch("steward.app._post_response_url", new_callable=AsyncMock) as post,
    ):
        body = (
            b"command=%2Fsteward-ask"
            b"&text=whats%20going%20on%20in%20the%20%23all-hacknight"
            b"&channel_id=C1&user_id=U1&response_url=https%3A%2F%2Fexample.com"
        )
        r = c.post("/api/v1/slack/commands", content=body, headers=_headers(body))
        assert r.status_code == 200
        _wait_awaited(post)
        rec.assert_not_awaited()
        posted = post.await_args.args[1]
        assert posted.strip() != "NOT DETERMINABLE"
        assert "NOT DETERMINABLE" not in posted
        assert "*TLDR*" in posted
        assert "*Summary*" in posted
        assert "*Attention / action required*" in posted
        assert "No Channel Memory for #all-hacknight yet" in posted
        assert "qdrant/qdrant" in posted


def test_mention_digest_intent_posts_shell_not_not_determinable(client):
    c, s, _ = client
    import steward.app as appmod

    appmod.bot_user_id = "UBOT"
    from datetime import datetime, timezone

    from steward.ledger import append_row

    now = datetime.now(timezone.utc).isoformat()
    append_row(
        s.ledger_path,
        {
            "origin": "github",
            "channel_id": None,
            "repo": "topoteretes/cognee",
            "permalink": "https://github.com/topoteretes/cognee/issues/2",
            "text": "issue #2: remember api",
            "occurred_at": now,
            "updated_at": now,
            "state": "open",
            "user_id": None,
            "kind": "issue",
        },
    )
    with (
        patch("steward.app.recall", new_callable=AsyncMock) as rec,
        patch("steward.app._ingest_github_since", new_callable=AsyncMock, return_value=1),
        patch("steward.app.channel_id_for_name", new_callable=AsyncMock, return_value="C0BP8V9S0UC"),
        patch("steward.app._slack_api", new_callable=AsyncMock, return_value={"ok": True}) as api,
    ):
        payload = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "channel": "C1",
                "user": "U1",
                "ts": "1.2",
                "text": "<@UBOT> whats going on in the #all-hacknight",
            },
        }
        import json

        raw = json.dumps(payload).encode()
        r = c.post(
            "/api/v1/slack/events",
            content=raw,
            headers={**_headers(raw), "Content-Type": "application/json"},
        )
        assert r.status_code == 200
        _wait_awaited(api)
        rec.assert_not_awaited()
        texts = [
            str(call.kwargs.get("text") or (call.args[3] if len(call.args) > 3 else ""))
            for call in api.await_args_list
        ]
        posted = " ".join(texts)
        if not posted.strip():
            posted = " ".join(str(call) for call in api.await_args_list)
        assert "NOT DETERMINABLE" not in posted
        assert "*TLDR*" in posted
        assert "No Channel Memory for #all-hacknight yet" in posted


def test_app_mention_posts_chat_message(client):
    c, s, _ = client
    import json

    import steward.app as appmod

    appmod.bot_user_id = "UBOT"
    with (
        patch("steward.app._compose_answer", new_callable=AsyncMock, return_value="SOURCED: hi") as compose,
        patch("steward.app._slack_api", new_callable=AsyncMock, return_value={"ok": True}) as api,
    ):
        payload = {
            "type": "event_callback",
            "event": {
                "type": "app_mention",
                "channel": "C1",
                "user": "U1",
                "ts": "9.9",
                "text": "<@UBOT> whats going on in the #all-hacknight",
            },
        }
        raw = json.dumps(payload).encode()
        r = c.post(
            "/api/v1/slack/events",
            content=raw,
            headers={**_headers(raw), "Content-Type": "application/json"},
        )
        assert r.status_code == 200
        _wait_awaited(api)
        compose.assert_awaited()
        assert compose.await_args.args[0] == "whats going on in the #all-hacknight"
        assert api.await_args.args[0] == "chat.postMessage"
        assert api.await_args.kwargs["channel"] == "C1"
        assert api.await_args.kwargs["text"] == "SOURCED: hi"
