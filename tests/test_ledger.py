from pathlib import Path
from steward.ledger import append_row, has_github_key, read_rows


def test_append_and_read(tmp_path: Path):
    path = tmp_path / "ingest.jsonl"
    append_row(path, {
        "origin": "remember",
        "channel_id": "C1",
        "repo": None,
        "permalink": "p1",
        "text": "hello",
        "occurred_at": "2026-08-14T10:00:00+02:00",
        "updated_at": None,
        "state": None,
        "user_id": "U1",
        "kind": "fact",
    })
    rows = read_rows(path)
    assert len(rows) == 1
    assert rows[0]["text"] == "hello"


def test_github_dedup_key(tmp_path: Path):
    path = tmp_path / "ingest.jsonl"
    append_row(path, {
        "origin": "github",
        "channel_id": None,
        "repo": "topoteretes/cognee",
        "permalink": "https://github.com/topoteretes/cognee/issues/1",
        "text": "issue",
        "occurred_at": "2026-08-14T10:00:00Z",
        "updated_at": "2026-08-14T10:00:00Z",
        "state": "open",
        "user_id": None,
        "kind": "issue",
    })
    assert has_github_key(
        path,
        "https://github.com/topoteretes/cognee/issues/1",
        "2026-08-14T10:00:00Z",
    )
    assert not has_github_key(
        path,
        "https://github.com/topoteretes/cognee/issues/1",
        "2026-08-14T11:00:00Z",
    )
