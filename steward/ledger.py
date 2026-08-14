from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def append_row(path: str | Path, row: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_rows(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    rows: list[dict[str, Any]] = []
    with p.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def has_github_key(path: str | Path, html_url: str, updated_at: str) -> bool:
    for row in read_rows(path):
        if row.get("origin") != "github":
            continue
        if row.get("permalink") == html_url and row.get("updated_at") == updated_at:
            return True
    return False
