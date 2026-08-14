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
from fastapi import BackgroundTasks, FastAPI, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from steward.allowlist import REFUSE_TEXT, is_allowed
from steward.config import Settings, load_settings
from steward.digest import is_digest_intent, parse_named_channel, render_digest, window_bounds
from steward.events import format_channel_memory_text, should_ingest_message
from steward.github_ingest import fetch_repo_issues, map_issue_to_memory, parse_repos
from steward.grounded import filter_hits_for_allowlist, format_grounded_answer
from steward.history import fetch_channel_history, messages_to_ingest
from steward.join_channels import channel_id_for_name, join_channel_ids, join_public_channels
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


ACK_TEXT = "Recalling…"
HACKNIGHT_CHANNEL_ID = "C0BP8V9S0UC"


async def _post_response_url(url: str, text: str, ephemeral: bool = True) -> None:
    payload = {
        "response_type": "ephemeral" if ephemeral else "in_channel",
        "text": text,
        "replace_original": True,
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


def _occurred_at(event: dict) -> str:
    ts = event.get("ts")
    if ts:
        try:
            return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat()
        except (TypeError, ValueError, OSError):
            pass
    return datetime.now(timezone.utc).isoformat()


def _archives_permalink(channel: str, ts: str) -> str:
    return f"https://slack.com/archives/{channel}/p{str(ts).replace('.', '')}"


async def _situation_digest(text: str, s: Settings) -> str:
    cid, name = parse_named_channel(text)
    if name and not cid:
        try:
            cid = await channel_id_for_name(name, s.slack_bot_token)
        except Exception:
            log.warning("channel lookup failed", exc_info=True)
            cid = None
    now = datetime.now(timezone.utc)
    start, end = window_bounds("weekly", s.digest_tz, now)
    since = start.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    try:
        await _ingest_github_since(since, s)
    except Exception:
        log.warning("github poll for situation failed", exc_info=True)
    rows = read_rows(s.ledger_path)
    return render_digest(
        "situation",
        rows,
        allowlist=s.memory_channels(),
        focus_channel_id=cid,
        focus_channel_name=name,
        start=start,
        end=end,
    )


async def _compose_answer(text: str, s: Settings) -> str:
    if is_digest_intent(text):
        return await _situation_digest(text, s)
    hits = await recall(text, datasets=[s.dataset_name])
    norm = []
    for h in hits:
        if isinstance(h, dict):
            norm.append(h)
        else:
            norm.append({"text": str(h), "origin": "unknown"})
    filtered = filter_hits_for_allowlist(norm, s.memory_channels())
    return format_grounded_answer(text, filtered)


async def _handle_ask(text: str, response_url: str, s: Settings) -> None:
    try:
        answer = await _compose_answer(text, s)
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


async def _remember_channel_event(event: dict, permalink: str, s: Settings) -> None:
    text = format_channel_memory_text(event, permalink)
    await remember_text(
        text,
        dataset_name=s.dataset_name,
        external_metadata={
            "origin": "slack_channel",
            "channel_id": event.get("channel"),
            "permalink": permalink,
        },
    )
    append_row(
        s.ledger_path,
        {
            "origin": "slack_channel",
            "channel_id": event.get("channel"),
            "repo": None,
            "permalink": permalink,
            "text": event.get("text") or "",
            "occurred_at": _occurred_at(event),
            "updated_at": None,
            "state": None,
            "user_id": event.get("user"),
            "kind": "message",
        },
    )


def _already_ingested(channel_id: str, ts: str, s: Settings) -> bool:
    if not ts:
        return False
    compact = ts.replace(".", "")
    for row in read_rows(s.ledger_path):
        if row.get("origin") != "slack_channel":
            continue
        if row.get("channel_id") != channel_id:
            continue
        perm = row.get("permalink") or ""
        if ts in perm or compact in perm:
            return True
    return False


async def _backfill_channel(s: Settings, channel_id: str) -> None:
    out = await fetch_channel_history(s.slack_bot_token, channel_id)
    if out.get("error"):
        log.warning("history %s: %s", channel_id, out["error"])
        return
    for item in messages_to_ingest(out["messages"], channel_id, bot_user_id or ""):
        ev = item["event"]
        ts = ev.get("ts") or ""
        if _already_ingested(channel_id, ts, s):
            continue
        permalink = _archives_permalink(channel_id, ts)
        try:
            await _remember_channel_event(ev, permalink, s)
        except Exception:
            log.exception("backfill ingest failed ts=%s", ts)


async def _handle_event_message(event: dict, s: Settings) -> None:
    global bot_user_id
    text = event.get("text") or ""
    channel = event.get("channel")
    if bot_user_id and f"<@{bot_user_id}>" in text:
        if is_allowed(channel or "", s.allowlist_channels):
            try:
                answer = await _compose_answer(text, s)
                await _slack_api(
                    "chat.postMessage",
                    s.slack_bot_token,
                    channel=channel,
                    text=answer,
                )
            except Exception:
                log.exception("mention ask failed")
        return
    gate = s.memory_channels() if s.ingest_channels else None
    if not should_ingest_message(event, bot_user_id or "", ingest_channels=gate):
        return
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
    try:
        await _remember_channel_event(event, permalink, s)
    except Exception:
        log.exception("channel ingest failed")


async def _after_ack(coro) -> None:
    """Schedule work after Slack has the 200. Do not await Cognee here."""
    asyncio.create_task(coro)


async def _startup_background(s: Settings) -> None:
    global bot_user_id
    try:
        await asyncio.to_thread(ensure_qdrant_adapter)
    except Exception:
        log.warning("qdrant adapter init failed", exc_info=True)
    try:
        auth = await _slack_api("auth.test", s.slack_bot_token)
        bot_user_id = auth.get("user_id")
    except Exception:
        log.warning("auth.test failed", exc_info=True)
    await _warm_start(s)


async def _warm_start(s: Settings) -> None:
    try:
        await join_public_channels(s.slack_bot_token)
    except Exception:
        log.warning("join channels failed", exc_info=True)
    try:
        ids = list(s.memory_channels())
        if HACKNIGHT_CHANNEL_ID not in ids:
            ids.append(HACKNIGHT_CHANNEL_ID)
        join_results = await join_channel_ids(s.slack_bot_token, ids)
        for cid, status in join_results.items():
            log.warning("join %s: %s", cid, status)
    except Exception:
        log.warning("ingest join failed", exc_info=True)
    try:
        await _backfill_channel(s, HACKNIGHT_CHANNEL_ID)
    except Exception:
        log.warning("history backfill failed", exc_info=True)
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
    global scheduler, settings
    # Listen first. Cognee register, join-all, and Qdrant stay off this path.
    if os.getenv("STEWARD_SKIP_STARTUP") == "1" or not os.getenv("SLACK_BOT_TOKEN"):
        yield
        return
    settings = load_settings()
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
    asyncio.create_task(_startup_background(settings))
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


def _ack() -> JSONResponse:
    return JSONResponse({"response_type": "ephemeral", "text": ACK_TEXT})


@app.post("/api/v1/slack/commands")
async def slack_commands(request: Request, background_tasks: BackgroundTasks):
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
        background_tasks.add_task(_after_ack, _handle_ask(text, response_url, s))
        return _ack()

    if command == "/steward-remember":
        if not text:
            return JSONResponse({"response_type": "ephemeral", "text": "Usage: /steward-remember <fact>"})
        background_tasks.add_task(
            _after_ack, _handle_remember(text, channel_id, user_id, response_url, s)
        )
        return _ack()

    if command == "/steward-digest":
        kind = text.lower().strip()
        if kind not in ("daily", "weekly"):
            return JSONResponse(
                {"response_type": "ephemeral", "text": "Usage: /steward-digest daily|weekly"}
            )
        background_tasks.add_task(_after_ack, _handle_digest(kind, response_url, s))
        return _ack()

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
