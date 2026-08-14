from __future__ import annotations

import re

_STOP = {
    "the", "a", "an", "is", "are", "of", "to", "in", "on", "for", "and", "or",
    "where", "who", "what", "we", "never", "mentioned", "company",
}


def filter_hits_for_allowlist(hits: list[dict], allowlist: list[str]) -> list[dict]:
    allowed = set(allowlist)
    out = []
    for h in hits:
        if h.get("origin") == "slack_channel" and h.get("channel_id") not in allowed:
            continue
        out.append(h)
    return out


def _tokens(s: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+", s.lower()) if t not in _STOP and len(t) > 2}


def format_grounded_answer(question: str, hits: list[dict]) -> str:
    q = _tokens(question)
    if not q:
        return "NOT DETERMINABLE"
    for h in hits:
        text = h.get("text") or ""
        if q & _tokens(text):
            link = h.get("permalink") or ""
            return f"SOURCED: {text.strip()} ({link})".strip()
    return "NOT DETERMINABLE"
