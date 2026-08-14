from __future__ import annotations

import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

SUMMARY_BLOCK_CAP = 20
SUMMARY_TOTAL_CAP = 40
TLDR_CAP = 5

_INTENT = re.compile(
    r"(what'?s\s+going\s+on|what\s+is\s+going\s+on|catch\s+me\s+up)",
    re.I,
)
_SLACK_CH = re.compile(r"<#([A-Z0-9]+)\|([^>]+)>")
_HASH_CH = re.compile(r"#([a-z0-9][a-z0-9._-]*)", re.I)


def is_digest_intent(text: str) -> bool:
    return bool(_INTENT.search(text or ""))


def parse_named_channel(text: str) -> tuple[str | None, str | None]:
    raw = text or ""
    m = _SLACK_CH.search(raw)
    if m:
        return m.group(1), m.group(2)
    m = _HASH_CH.search(raw)
    if m:
        return None, m.group(1)
    return None, None


def window_bounds(kind: str, tz_name: str, now: datetime) -> tuple[datetime, datetime]:
    tz = ZoneInfo(tz_name)
    if now.tzinfo is None:
        now = now.replace(tzinfo=tz)
    else:
        now = now.astimezone(tz)
    if kind == "daily":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif kind == "weekly":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start = start.fromordinal(start.toordinal() - start.weekday())
        start = start.replace(tzinfo=tz)
    else:
        raise ValueError(f"unknown digest kind: {kind}")
    return start, now


def _parse_ts(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _in_window(row: dict, start: datetime, end: datetime) -> bool:
    ts = _parse_ts(row.get("updated_at") or row.get("occurred_at"))
    if ts is None:
        return False
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=start.tzinfo)
    return start <= ts <= end


def _bullet(text: str, permalink: str) -> str:
    return f"• {text} <{permalink}|permalink>"


def render_digest(
    kind: str,
    rows: list[dict[str, Any]],
    allowlist: list[str],
    title_day: str = "",
    channel_names: dict[str, str] | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    focus_channel_id: str | None = None,
    focus_channel_name: str | None = None,
) -> str:
    channel_names = channel_names or {}
    allowed = set(allowlist)
    focus_name = (focus_channel_name or "").lstrip("#") or None

    if start is not None and end is not None:
        rows = [r for r in rows if _in_window(r, start, end)]

    if focus_channel_id or focus_name:
        slack_rows = [
            r
            for r in rows
            if r.get("origin") == "slack_channel"
            and (not focus_channel_id or r.get("channel_id") == focus_channel_id)
        ]
        if focus_channel_id and focus_name:
            channel_names = {**channel_names, focus_channel_id: focus_name}
    else:
        # remember without channel still counts under Slack if channel_id on allowlist or None
        slack_rows = [
            r
            for r in rows
            if r.get("origin") in ("slack_channel", "remember")
            and r.get("origin") != "seed"
            and (r.get("channel_id") is None or r.get("channel_id") in allowed)
            and not (r.get("origin") == "slack_channel" and r.get("channel_id") not in allowed)
        ]
    github_rows = [r for r in rows if r.get("origin") == "github"]

    summary_bullets: list[tuple[str, str, str]] = []  # (section, text, permalink)
    slack_by_ch: dict[str, list[dict]] = {}
    for r in slack_rows:
        if (
            not (focus_channel_id or focus_name)
            and r.get("origin") == "slack_channel"
            and r.get("channel_id") not in allowed
        ):
            continue
        cid = r.get("channel_id") or "_facts"
        slack_by_ch.setdefault(cid, []).append(r)

    sections: list[str] = []
    label = kind
    header = f"*Steward {label} digest"
    if title_day:
        header += f" — {title_day}"
    header += "*"

    # Slack blocks
    slack_section_lines: list[str] = []
    total = 0
    overflow = 0
    for cid, items in slack_by_ch.items():
        name = channel_names.get(cid, cid if cid != "_facts" else "facts")
        block_lines: list[str] = []
        for r in items[:SUMMARY_BLOCK_CAP]:
            if total >= SUMMARY_TOTAL_CAP:
                overflow += 1
                continue
            uid = r.get("user_id")
            prefix = f"<@{uid}>: " if uid else ""
            line = _bullet(f"{prefix}{r.get('text', '')}", r.get("permalink") or "")
            block_lines.append(line)
            summary_bullets.append(("slack", r.get("text", ""), r.get("permalink") or ""))
            total += 1
        if len(items) > SUMMARY_BLOCK_CAP:
            overflow += len(items) - SUMMARY_BLOCK_CAP
        ch_label = f"#{name}" if cid != "_facts" else name
        slack_section_lines.append(f"*Slack · {ch_label}*")
        if block_lines:
            slack_section_lines.extend(block_lines)
        else:
            slack_section_lines.append("_No remembered channel activity in this window._")

    if not slack_by_ch:
        if focus_name or focus_channel_id:
            ch = focus_name or focus_channel_id
            slack_section_lines.append(f"*Slack · #{ch}*")
            slack_section_lines.append(f"No Channel Memory for #{ch} yet")
        else:
            slack_section_lines.append("*Slack*")
            slack_section_lines.append("_No remembered channel activity in this window._")

    # GitHub blocks
    gh_by_repo: dict[str, list[dict]] = {}
    for r in github_rows:
        gh_by_repo.setdefault(r.get("repo") or "unknown", []).append(r)

    gh_section_lines: list[str] = []
    for repo, items in sorted(gh_by_repo.items()):
        block_lines = []
        for r in items[:SUMMARY_BLOCK_CAP]:
            if total >= SUMMARY_TOTAL_CAP:
                overflow += 1
                continue
            line = _bullet(r.get("text", ""), r.get("permalink") or "")
            block_lines.append(line)
            summary_bullets.append(("github", r.get("text", ""), r.get("permalink") or ""))
            total += 1
        if len(items) > SUMMARY_BLOCK_CAP:
            overflow += len(items) - SUMMARY_BLOCK_CAP
        gh_section_lines.append(f"*GitHub · {repo}*")
        if block_lines:
            gh_section_lines.extend(block_lines)
        else:
            gh_section_lines.append("_No issue/PR updates in this window._")

    if overflow:
        gh_section_lines.append(f"_{overflow} more in ledger, not shown._")

    # TLDR from newest summary bullets (already roughly ordered by input)
    tldr = summary_bullets[:TLDR_CAP]
    tldr_lines = [_bullet(t, p) for _, t, p in tldr] or ["_None in this window._"]

    # Attention: open github
    attn = [
        r
        for r in github_rows
        if (r.get("state") or "").lower() == "open"
    ]
    attn_lines = [
        _bullet(r.get("text", ""), r.get("permalink") or "") for r in attn[:SUMMARY_BLOCK_CAP]
    ] or ["_None in this window._"]

    parts = [
        header,
        "",
        "*TLDR*",
        *tldr_lines,
        "",
        "*Summary*",
        *slack_section_lines,
        *gh_section_lines,
        "",
        "*Attention / action required*",
        *attn_lines,
    ]
    return "\n".join(parts)
