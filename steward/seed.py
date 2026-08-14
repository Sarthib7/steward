from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path

from steward.ledger import append_row, read_rows
from steward.memory import ensure_qdrant_adapter, remember_text

log = logging.getLogger(__name__)


async def seed_docs(path: str = "docs/seed", dataset_name: str = "steward", ledger_path: str = ".steward/ingest.jsonl") -> int:
    ensure_qdrant_adapter()
    root = Path(path)
    if not root.exists():
        log.warning("seed path missing: %s", path)
        return 0
    existing = {
        r.get("permalink")
        for r in read_rows(ledger_path)
        if r.get("origin") == "seed"
    }
    count = 0
    for md in sorted(root.glob("*.md")):
        name = md.name
        if name in existing:
            continue
        text = md.read_text(encoding="utf-8")
        body = f"[Seed Doc] filename={name}\n{text}"
        await remember_text(
            body,
            dataset_name=dataset_name,
            external_metadata={"permalink": name, "origin": "seed"},
        )
        append_row(
            ledger_path,
            {
                "origin": "seed",
                "channel_id": None,
                "repo": None,
                "permalink": name,
                "text": text[:500],
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": None,
                "state": None,
                "user_id": None,
                "kind": "seed",
            },
        )
        count += 1
    return count
