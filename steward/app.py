from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from steward.allowlist import REFUSE_TEXT, is_allowed
from steward.config import Settings, load_settings
from steward.digest import render_digest, window_bounds
from steward.events import format_channel_memory_text, should_ingest_message
from steward.github_ingest import fetch_repo_issues, map_issue_to_memory, parse_repos
from steward.grounded import filter_hits_for_allowlist, format_grounded_answer
from steward.join_channels import join_channel_ids, join_public_channels
from steward.ledger import append_row, has_github_key, read_rows
from steward.memory import ensure_qdrant_adapter, recall, remember_text
from steward.slack_verify import verify_slack_signature

load_dotenv()
log = logging.getLogger(__name__)

settings: Settings | None = None
bot_user_id: str | None = None
scheduler: AsyncIOScheduler | None = None


def get_settings() -> Settings:
    global settings
    if settings is None:
        settings = load_settings()
    return settings


async def _post_response_url(url: str, text: str, ephemeral: bool = True) -> None:
    payload = {
        "response_type": "ephemeral" if ephemeral else "in_channel",
        "text": text,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            await client.post(url, json=payload)
    except httpx.HTTPError as e:
        log.warning("response_url failed: %s", e)


async def _slack_api(method: str, token: str, **params: Any) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            f"https://slack.com/api/{method}",
            headers={"Authorization": f"Bearer {token}"},
            data=params,
        )
        return r.json()


async def _ingest_github_since(since: str, s: Settings) -> int:
    added = 0
    async with httpx.AsyncClient(timeout=30.0) as client:
        for owner, repo in parse_repos(s.github_repos):
            items = await fetch_repo_issues(
                owner, repo, since, token=s.github_token, client=client
            )
            full = f"{owner}/{repo}"
            for item in items:
                mapped = map_issue_to_memory(item, full)
                row = mapped["ledger_row"]
                if has_github_key(s.ledger_path, row["permalink"], row["updated_at"] or ""):
                    continue
                await remember_text(
                    mapped["text"],
                    dataset_name=s.dataset_name,
                    external_metadata=mapped["metadata"],
                )
                append_row(s.ledger_path, row)
                added += 1
    return added


async def _handle_ask(text: str, response_url: str, s: Settings) -> None:
    try:
        hits = await recall(text, datasets=[s.dataset_name])
        # Normalize hits that may be strings
        norm = []
        for h in hits:
            if isinstance(h, dict):
                norm.append(h)
            else:
                norm.append({"text": str(h), "origin": "unknown"})
        filtered = filter_hits_for_allowlist(norm, s.memory_channels())
        answer = format_grounded_answer(text, filtered)
        await _post_response_url(response_url, answer)
    except Exception:
        log.exception("ask failed")
        await _post_response_url(response_url, "Something went wrong")


async def _handle_remember(text: str, channel_id: str, user_id: str, response_url: str, s: Settings) -> None:
    try:
        body = f"[Remembered Fact] channel={channel_id} user={user_id}\n{text}"
        await remember_text(
            body,
            dataset_name=s.dataset_name,
            external_metadata={"origin": "remember", "channel_id": channel_id, "permalink": "cmd"},
        )
        append_row(
            s.ledger_path,
            {
                "origin": "remember",
                "channel_id": channel_id,
                "repo": None,
                "permalink": "cmd",
                "text": text,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": None,
                "state": None,
                "user_id": user_id,
                "kind": "fact",
            },
        )
        await _post_response_url(response_url, "Remembered.")
    except Exception:
        log.exception("remember failed")
        await _post_response_url(response_url, "Something went wrong")


async def _handle_digest(kind: str, response_url: str, s: Settings) -> None:
    try:
        tz = s.digest_tz
        now = datetime.now(timezone.utc)
        start, end = window_bounds(kind, tz, now)
        since = start.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        await _ingest_github_since(since, s)
        rows = read_rows(s.ledger_path)
        # filter by window
        body = render_digest(
            kind,
            rows,
            allowlist=s.memory_channels(),
            title_day=end.strftime("%a %d %b"),
            start=start,
            end=end,
        )
        await _post_response_url(response_url, body)
    except Exception:
        log.exception("digest failed")
        await _post_response_url(response_url, "Something went wrong")


async def _handle_event_message(event: dict, s: Settings) -> None:
    global bot_user_id
    gate = s.memory_channels() if s.ingest_channels else None
    if not should_ingest_message(event, bot_user_id or "", ingest_channels=gate):
        return
    channel = event.get("channel")
    ts = event.get("ts")
    permalink = f"slack://channel?team=&id={channel}&message={ts}"
    try:
        data = await _slack_api(
            "chat.getPermalink",
            s.slack_bot_token,
            channel=channel,
            message_ts=ts,
        )
        if data.get("ok") and data.get("permalink"):
            permalink = data["permalink"]
    except Exception:
        log.warning("permalink fetch failed", exc_info=True)
    text = format_channel_memory_text(event, permalink)
    try:
        await remember_text(
            text,
            dataset_name=s.dataset_name,
            external_metadata={
                "origin": "slack_channel",
                "channel_id": channel,
                "permalink": permalink,
            },
        )
        append_row(
            s.ledger_path,
            {
                "origin": "slack_channel",
                "channel_id": channel,
                "repo": None,
                "permalink": permalink,
                "text": event.get("text") or "",
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": None,
                "state": None,
                "user_id": event.get("user"),
                "kind": "message",
            },
        )
    except Exception:
        log.exception("channel ingest failed")


async def _warm_start(s: Settings) -> None:
    try:
        await join_public_channels(s.slack_bot_token)
    except Exception:
        log.warning("join channels failed", exc_info=True)
    try:
        join_results = await join_channel_ids(
            s.slack_bot_token, s.memory_channels()
        )
        for cid, status in join_results.items():
            log.warning("join %s: %s", cid, status)
    except Exception:
        log.warning("ingest join failed", exc_info=True)
    try:
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat().replace("+00:00", "Z")
        await _ingest_github_since(since, s)
    except Exception:
        log.warning("github warm pull failed", exc_info=True)


async def _cron_digest(kind: str) -> None:
    s = get_settings()
    if not is_allowed(s.digest_channel, s.allowlist_channels):
        log.warning("digest channel not on allowlist; skip cron")
        return
    stamp = Path(f".steward/last_{kind}_digest")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if stamp.exists() and stamp.read_text().strip() == today and kind == "daily":
        return
    try:
        now = datetime.now(timezone.utc)
        start, end = window_bounds(kind, s.digest_tz, now)
        since = start.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        await _ingest_github_since(since, s)
        body = render_digest(
            kind,
            read_rows(s.ledger_path),
            allowlist=s.memory_channels(),
            title_day=end.strftime("%a %d %b"),
            start=start,
            end=end,
        )
        data = await _slack_api(
            "chat.postMessage",
            s.slack_bot_token,
            channel=s.digest_channel,
            text=body,
        )
        if not data.get("ok"):
            log.warning("cron postMessage failed: %s", data.get("error"))
            return
        stamp.parent.mkdir(parents=True, exist_ok=True)
        stamp.write_text(today if kind == "daily" else end.strftime("%G-W%V"))
    except Exception:
        log.exception("cron digest failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_user_id, scheduler, settings
    # Allow import/test without full env
    if os.getenv("STEWARD_SKIP_STARTUP") != "1":
        ensure_qdrant_adapter()
    if os.getenv("STEWARD_SKIP_STARTUP") == "1" or not os.getenv("SLACK_BOT_TOKEN"):
        yield
        return
    settings = load_settings()
    try:
        auth = await _slack_api("auth.test", settings.slack_bot_token)
        bot_user_id = auth.get("user_id")
    except Exception:
        log.warning("auth.test failed", exc_info=True)

    scheduler = AsyncIOScheduler(timezone=settings.digest_tz)
    weekday = settings.digest_weekday
    hour = settings.digest_hour
    scheduler.add_job(_cron_digest, "cron", args=["daily"], hour=hour, minute=0, id="daily")
    scheduler.add_job(
        _cron_digest,
        "cron",
        args=["weekly"],
        day_of_week=weekday,
        hour=hour,
        minute=5,
        id="weekly",
    )
    scheduler.start()
    asyncio.create_task(_warm_start(settings))
    yield
    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(title="steward", lifespan=lifespan)


def _verify_request(request: Request, body: bytes, s: Settings) -> bool:
    return verify_slack_signature(
        s.slack_signing_secret,
        body,
        request.headers.get("X-Slack-Request-Timestamp", ""),
        request.headers.get("X-Slack-Signature", ""),
    )


@app.post("/api/v1/slack/commands")
async def slack_commands(request: Request):
    body = await request.body()
    s = get_settings()
    if not _verify_request(request, body, s):
        return Response(status_code=401)
    form = {k: v[0] for k, v in parse_qs(body.decode()).items()}
    channel_id = form.get("channel_id", "")
    command = form.get("command", "")
    text = (form.get("text") or "").strip()
    user_id = form.get("user_id", "")
    response_url = form.get("response_url", "")

    if not is_allowed(channel_id, s.allowlist_channels):
        return JSONResponse({"response_type": "ephemeral", "text": REFUSE_TEXT})

    if command == "/steward-ask":
        if not text:
            return JSONResponse({"response_type": "ephemeral", "text": "Usage: /steward-ask <question>"})
        asyncio.create_task(_handle_ask(text, response_url, s))
        return Response(status_code=200)

    if command == "/steward-remember":
        if not text:
            return JSONResponse({"response_type": "ephemeral", "text": "Usage: /steward-remember <fact>"})
        asyncio.create_task(_handle_remember(text, channel_id, user_id, response_url, s))
        return Response(status_code=200)

    if command == "/steward-digest":
        kind = text.lower().strip()
        if kind not in ("daily", "weekly"):
            return JSONResponse(
                {"response_type": "ephemeral", "text": "Usage: /steward-digest daily|weekly"}
            )
        asyncio.create_task(_handle_digest(kind, response_url, s))
        return Response(status_code=200)

    return JSONResponse({"response_type": "ephemeral", "text": "Unknown command"})


@app.post("/api/v1/slack/events")
async def slack_events(request: Request):
    body = await request.body()
    payload = await request.json()
    if payload.get("type") == "url_verification":
        return PlainTextResponse(payload["challenge"])

    s = get_settings()
    if not _verify_request(request, body, s):
        return Response(status_code=401)

    event = payload.get("event") or {}
    if event.get("type") == "message" and "channel" in event:
        asyncio.create_task(_handle_event_message(event, s))
    return Response(status_code=200)


@app.get("/health")
async def health():
    return {"ok": True}
