from __future__ import annotations


def should_ingest_message(event: dict, bot_user_id: str, ingest_channels: list[str] | None = None) -> bool:
    if event.get("subtype") == "bot_message" or event.get("bot_id"):
        return False
    text = (event.get("text") or "").strip()
    if not text:
        return False
    if event.get("user") == bot_user_id:
        return False
    if text.startswith("/"):
        return False
    if ingest_channels is not None and event.get("channel") not in set(ingest_channels):
        return False
    return True


def format_channel_memory_text(event: dict, permalink: str) -> str:
    return (
        f"[Channel Memory] channel={event.get('channel')} user={event.get('user')} "
        f"ts={event.get('ts')} permalink={permalink}\n{event.get('text')}"
    )
