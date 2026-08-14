# Steward Slice 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a laptop FastAPI Slack bot that remembers public-channel chat plus two public GitHub repos into Cognee/Qdrant Cloud, answers with `SOURCED` / `NOT DETERMINABLE` on an allowlist, and posts daily/weekly Digests (TLDR → Summary → Attention) via slash and APScheduler.

**Architecture:** One FastAPI process on port 8000 (cognee-demo-slack shape: signing secret, 3s ack, `response_url`). Writes go through `cognee.remember` into dataset `steward` and an append-only `.steward/ingest.jsonl` ledger. Ask uses `cognee.recall` then allowlist-filters Channel Memory hits. Digest reads the ledger only. GitHub is REST poll (issues including PRs), not webhooks. No Person Rollup. No Linear client.

**Tech Stack:** Python 3.11+, FastAPI, httpx, APScheduler, Cognee pin `cognee[fastembed] @ git+https://github.com/topoteretes/cognee.git@dev`, `cognee-community-vector-adapter-qdrant==0.4.0` (demo install flags), Qdrant Cloud, OpenRouter DeepSeek V4 Flash, Slack Bot + Events API, ngrok for HTTPS.

**Design source:** [`docs/superpowers/specs/2026-08-14-steward-slice1-design.md`](../specs/2026-08-14-steward-slice1-design.md) (approved 2026-08-14). Vocabulary: [`CONTEXT.md`](../../../CONTEXT.md).

## Global Constraints

- Cognee pin: `cognee[fastembed] @ git+https://github.com/topoteretes/cognee.git@dev` (research tip `1.5.0.dev1`); `remember()` only, no bare `http(s)` as `data`, no `session_id` for permanent writes.
- Vector adapter: `cognee-community-vector-adapter-qdrant==0.4.0` with `--no-deps --ignore-requires-python` (demo shape).
- `ENABLE_BACKEND_ACCESS_CONTROL=false`. Dataset name: `steward`.
- LLM: `LLM_PROVIDER=custom`, `LLM_MODEL=openrouter/deepseek/deepseek-v4-flash-0731`, `LLM_ENDPOINT=https://openrouter.ai/api/v1`.
- Embeddings default: `EMBEDDING_PROVIDER=fastembed`, `EMBEDDING_MODEL=BAAI/bge-small-en-v1.5`, `EMBEDDING_DIMENSIONS=384`.
- TZ: `STEWARD_DIGEST_TZ=Europe/Berlin`. Weekly cron weekday default `mon`. Daily/weekly hour default `8`.
- GitHub: `GITHUB_REPOS=topoteretes/cognee,qdrant/qdrant`, issues+PRs only (no releases, no commits endpoint, no webhooks). Cap 100/repo/pull.
- Allowlist: `STEWARD_ALLOWLIST_CHANNELS` + `STEWARD_DIGEST_CHANNEL` (must be on allowlist). Refuse copy equivalent to `Steward isn't enabled here`.
- Digest format: TLDR → Summary (Slack then GitHub) → Attention/action. Template only (no LLM rewrite). No Person Rollup. No Linear.
- Host: laptop + ngrok. No live Slack/GitHub/Qdrant in unit tests.
- Secrets stay in `.env` / gitignored files. Never commit keys. Never paste `steward_api_key.txt` contents into docs or chat.
- Do not vendor Scout or Citadel. Do not add Linear stub packages.

---

## File structure (create)

```
steward/
  __init__.py
  __main__.py              # python -m steward seed
  config.py                # env settings
  app.py                   # FastAPI + routes + scheduler lifespan
  slack_verify.py          # signature check
  allowlist.py             # channel allowlist helpers
  ledger.py                # .steward/ingest.jsonl
  memory.py                # cognee remember/recall wrappers
  grounded.py              # SOURCED / NOT DETERMINABLE from recall hits
  events.py                # message.channels ingest rules
  github_ingest.py         # REST issues poll + format + dedup
  digest.py                # window + TLDR/Summary/Attention renderer
  seed.py                  # docs/seed/ ingest
  join_channels.py         # startup public join
tests/
  test_slack_verify.py
  test_allowlist.py
  test_ledger.py
  test_grounded.py
  test_events.py
  test_github_ingest.py
  test_digest.py
  test_commands.py
docs/seed/
  steward-overview.md
.env.example
requirements.txt
pyproject.toml             # optional; requirements.txt is enough for hack
slack-manifest.json
README.md                  # update run/ngrok section only when app exists
```

---

### Task 1: Project scaffold and env template

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `steward/__init__.py`
- Create: `pyproject.toml` (minimal pytest package layout)
- Modify: `.gitignore` only if `.steward/` is missing

**Interfaces:**
- Consumes: nothing
- Produces: installable test layout; documented env names for later tasks

- [ ] **Step 1: Write `requirements.txt`**

```text
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
httpx>=0.27.0
apscheduler>=3.10.0
python-dotenv>=1.0.0
pytest>=8.0.0
pytest-asyncio>=0.24.0
```

Add a short comment at the top of the file (or a `Makefile` / README note later) that Cognee and the Qdrant adapter install separately:

```bash
pip install -r requirements.txt
pip install "cognee[fastembed] @ git+https://github.com/topoteretes/cognee.git@dev"
pip install "cognee-community-vector-adapter-qdrant==0.4.0" --no-deps --ignore-requires-python
```

- [ ] **Step 2: Write `.env.example` (no real secrets)**

```bash
SLACK_SIGNING_SECRET=
SLACK_BOT_TOKEN=
STEWARD_ALLOWLIST_CHANNELS=
STEWARD_DIGEST_CHANNEL=
STEWARD_DIGEST_TZ=Europe/Berlin
STEWARD_DIGEST_HOUR=8
STEWARD_DIGEST_WEEKDAY=mon

LLM_PROVIDER=custom
LLM_MODEL=openrouter/deepseek/deepseek-v4-flash-0731
LLM_ENDPOINT=https://openrouter.ai/api/v1
LLM_API_KEY=

EMBEDDING_PROVIDER=fastembed
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_DIMENSIONS=384

VECTOR_DB_PROVIDER=qdrant
VECTOR_DATASET_DATABASE_HANDLER=qdrant
VECTOR_DB_URL=
VECTOR_DB_KEY=
ENABLE_BACKEND_ACCESS_CONTROL=false

GITHUB_REPOS=topoteretes/cognee,qdrant/qdrant
GITHUB_TOKEN=
```

- [ ] **Step 3: Create package stubs and pytest config**

```python
# steward/__init__.py
__version__ = "0.1.0"
```

```toml
# pyproject.toml
[project]
name = "steward"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
pythonpath = ["."]
```

Ensure `.gitignore` includes `.steward/`, `.env`, and `steward_api_key.txt` (already present for secrets).

- [ ] **Step 4: Install deps and confirm pytest collects zero failing empty suite**

Run: `pip install -r requirements.txt && pytest -q`
Expected: `no tests ran` or `0 passed` with exit 0.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .env.example steward/__init__.py pyproject.toml .gitignore
git commit -m "$(cat <<'EOF'
chore: scaffold steward package and env template

EOF
)"
```

---

### Task 2: Config loader

**Files:**
- Create: `steward/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Consumes: environment variables from Task 1
- Produces: `Settings` dataclass / simple namespace with typed fields used by later tasks

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
import os
from steward.config import load_settings

def test_load_settings_parses_allowlist_and_defaults(monkeypatch):
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "sig")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("STEWARD_ALLOWLIST_CHANNELS", "C1, C2")
    monkeypatch.setenv("STEWARD_DIGEST_CHANNEL", "C1")
    monkeypatch.setenv("LLM_API_KEY", "or-key")
    monkeypatch.setenv("VECTOR_DB_URL", "https://example.qdrant.io")
    monkeypatch.setenv("VECTOR_DB_KEY", "q-key")
    for k in ("STEWARD_DIGEST_TZ", "GITHUB_REPOS", "LLM_MODEL"):
        monkeypatch.delenv(k, raising=False)

    s = load_settings()
    assert s.allowlist_channels == ["C1", "C2"]
    assert s.digest_channel == "C1"
    assert s.digest_tz == "Europe/Berlin"
    assert s.github_repos == ["topoteretes/cognee", "qdrant/qdrant"]
    assert s.llm_model == "openrouter/deepseek/deepseek-v4-flash-0731"
    assert s.dataset_name == "steward"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py::test_load_settings_parses_allowlist_and_defaults -v`
Expected: FAIL with `ModuleNotFoundError` or `ImportError`

- [ ] **Step 3: Write minimal implementation**

```python
# steward/config.py
from __future__ import annotations
from dataclasses import dataclass
import os

DEFAULT_GITHUB_REPOS = "topoteretes/cognee,qdrant/qdrant"
DEFAULT_LLM_MODEL = "openrouter/deepseek/deepseek-v4-flash-0731"

@dataclass(frozen=True)
class Settings:
    slack_signing_secret: str
    slack_bot_token: str
    allowlist_channels: list[str]
    digest_channel: str
    digest_tz: str
    digest_hour: int
    digest_weekday: str
    llm_provider: str
    llm_model: str
    llm_endpoint: str
    llm_api_key: str
    vector_db_url: str
    vector_db_key: str
    github_repos: list[str]
    github_token: str | None
    dataset_name: str = "steward"
    ledger_path: str = ".steward/ingest.jsonl"

def _csv(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [p.strip() for p in raw.split(",") if p.strip()]

def load_settings() -> Settings:
    return Settings(
        slack_signing_secret=os.environ["SLACK_SIGNING_SECRET"],
        slack_bot_token=os.environ["SLACK_BOT_TOKEN"],
        allowlist_channels=_csv("STEWARD_ALLOWLIST_CHANNELS"),
        digest_channel=os.getenv("STEWARD_DIGEST_CHANNEL", ""),
        digest_tz=os.getenv("STEWARD_DIGEST_TZ", "Europe/Berlin"),
        digest_hour=int(os.getenv("STEWARD_DIGEST_HOUR", "8")),
        digest_weekday=os.getenv("STEWARD_DIGEST_WEEKDAY", "mon"),
        llm_provider=os.getenv("LLM_PROVIDER", "custom"),
        llm_model=os.getenv("LLM_MODEL", DEFAULT_LLM_MODEL),
        llm_endpoint=os.getenv("LLM_ENDPOINT", "https://openrouter.ai/api/v1"),
        llm_api_key=os.environ["LLM_API_KEY"],
        vector_db_url=os.environ["VECTOR_DB_URL"],
        vector_db_key=os.environ["VECTOR_DB_KEY"],
        github_repos=_csv("GITHUB_REPOS", DEFAULT_GITHUB_REPOS),
        github_token=os.getenv("GITHUB_TOKEN") or None,
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add steward/config.py tests/test_config.py
git commit -m "$(cat <<'EOF'
feat: add steward settings loader with DeepSeek default

EOF
)"
```

---

### Task 3: Slack signature verification

**Files:**
- Create: `steward/slack_verify.py`
- Test: `tests/test_slack_verify.py`

**Interfaces:**
- Consumes: `signing_secret: str`
- Produces: `verify_slack_signature(secret, body: bytes, timestamp: str, signature: str) -> bool`

- [ ] **Step 1: Write failing tests (valid / invalid / expired)**

```python
# tests/test_slack_verify.py
import hashlib
import hmac
import time
from steward.slack_verify import verify_slack_signature

SECRET = "test_secret"

def _sig(secret: str, ts: str, body: bytes) -> str:
    base = b"v0:" + ts.encode() + b":" + body
    digest = hmac.new(secret.encode(), base, hashlib.sha256).hexdigest()
    return f"v0={digest}"

def test_valid_signature():
    body = b"command=%2Fsteward-ask&text=hi"
    ts = str(int(time.time()))
    assert verify_slack_signature(SECRET, body, ts, _sig(SECRET, ts, body)) is True

def test_invalid_signature():
    body = b"command=%2Fsteward-ask&text=hi"
    ts = str(int(time.time()))
    assert verify_slack_signature(SECRET, body, ts, "v0=deadbeef") is False

def test_expired_timestamp():
    body = b"command=%2Fsteward-ask&text=hi"
    ts = str(int(time.time()) - 60 * 10)
    assert verify_slack_signature(SECRET, body, ts, _sig(SECRET, ts, body)) is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_slack_verify.py -v`
Expected: FAIL import or assert

- [ ] **Step 3: Implement**

```python
# steward/slack_verify.py
from __future__ import annotations
import hashlib
import hmac
import time

MAX_AGE_SECONDS = 60 * 5

def verify_slack_signature(
    signing_secret: str,
    body: bytes,
    timestamp: str,
    signature: str,
) -> bool:
    try:
        ts = int(timestamp)
    except (TypeError, ValueError):
        return False
    if abs(time.time() - ts) > MAX_AGE_SECONDS:
        return False
    base = b"v0:" + timestamp.encode() + b":" + body
    expected = "v0=" + hmac.new(
        signing_secret.encode(), base, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature or "")
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_slack_verify.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add steward/slack_verify.py tests/test_slack_verify.py
git commit -m "$(cat <<'EOF'
feat: verify Slack request signatures

EOF
)"
```

---

### Task 4: Allowlist gate

**Files:**
- Create: `steward/allowlist.py`
- Test: `tests/test_allowlist.py`

**Interfaces:**
- Consumes: allowlist channel id list
- Produces: `is_allowed(channel_id, allowlist) -> bool`, `REFUSE_TEXT = "Steward isn't enabled here"`

- [ ] **Step 1: Write failing test**

```python
from steward.allowlist import REFUSE_TEXT, is_allowed

def test_on_list():
    assert is_allowed("C1", ["C1", "C2"]) is True

def test_off_list():
    assert is_allowed("C9", ["C1", "C2"]) is False

def test_refuse_copy():
    assert REFUSE_TEXT == "Steward isn't enabled here"
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_allowlist.py -v`

- [ ] **Step 3: Implement**

```python
# steward/allowlist.py
REFUSE_TEXT = "Steward isn't enabled here"

def is_allowed(channel_id: str | None, allowlist: list[str]) -> bool:
    if not channel_id:
        return False
    return channel_id in set(allowlist)
```

- [ ] **Step 4: Pass + commit**

```bash
git add steward/allowlist.py tests/test_allowlist.py
git commit -m "$(cat <<'EOF'
feat: add Slack channel allowlist gate

EOF
)"
```

---

### Task 5: Ingest Ledger

**Files:**
- Create: `steward/ledger.py`
- Test: `tests/test_ledger.py`

**Interfaces:**
- Consumes: filesystem path
- Produces: `LedgerRow` typed dict / dataclass; `append_row(path, row)`; `read_rows(path)`; `has_github_key(path, html_url, updated_at) -> bool`

Ledger row fields (design):

```python
{
  "origin": "slack_channel" | "remember" | "seed" | "github",
  "channel_id": str | None,
  "repo": str | None,
  "permalink": str,
  "text": str,
  "occurred_at": str,  # ISO-8601
  "updated_at": str | None,
  "state": str | None,  # github open/closed
  "user_id": str | None,
  "kind": str | None,   # issue | pull_request | fact | message | seed
}
```

- [ ] **Step 1: Write failing tests**

```python
# tests/test_ledger.py
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
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_ledger.py -v`

- [ ] **Step 3: Implement append-only JSONL**

```python
# steward/ledger.py
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
```

- [ ] **Step 4: Pass + commit**

```bash
git add steward/ledger.py tests/test_ledger.py
git commit -m "$(cat <<'EOF'
feat: add append-only ingest ledger

EOF
)"
```

---

### Task 6: Grounded Answer filter (no Cognee yet)

**Files:**
- Create: `steward/grounded.py`
- Test: `tests/test_grounded.py`

**Interfaces:**
- Consumes: recall hit list shaped as `{text, channel_id?, permalink?, origin?}`
- Produces: `filter_hits_for_allowlist(hits, allowlist) -> hits`; `format_grounded_answer(question, hits) -> str` emitting `SOURCED` or `NOT DETERMINABLE`

Design rule: drop Channel Memory hits whose `channel_id` is off-allowlist. Keep github / seed / remember. If no remaining hit addresses the question, `NOT DETERMINABLE`. Slice 1 heuristic: treat a hit as addressing when any significant token from the question appears in hit text (simple containment); do not add a second LLM pass.

- [ ] **Step 1: Write failing tests**

```python
from steward.grounded import filter_hits_for_allowlist, format_grounded_answer

def test_drops_off_allowlist_channel_memory():
    hits = [
        {"origin": "slack_channel", "channel_id": "C9", "text": "vectors in qdrant", "permalink": "p9"},
        {"origin": "github", "channel_id": None, "text": "issue about qdrant", "permalink": "https://github.com/qdrant/qdrant/issues/1"},
        {"origin": "seed", "channel_id": None, "text": "vectors live on Qdrant Cloud", "permalink": "steward-overview.md"},
    ]
    kept = filter_hits_for_allowlist(hits, ["C1"])
    assert [h["origin"] for h in kept] == ["github", "seed"]

def test_sourced_when_hit_matches():
    hits = [{"origin": "remember", "text": "vectors live on Qdrant Cloud", "permalink": "cmd"}]
    out = format_grounded_answer("where are vectors stored?", hits)
    assert "SOURCED" in out
    assert "Qdrant Cloud" in out

def test_not_determinable_on_noise():
    hits = [{"origin": "remember", "text": "lunch is at noon", "permalink": "cmd"}]
    out = format_grounded_answer("who is the CEO of a company we never mentioned?", hits)
    assert out.strip() == "NOT DETERMINABLE"
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_grounded.py -v`

- [ ] **Step 3: Implement minimal matcher**

```python
# steward/grounded.py
from __future__ import annotations
import re

_STOP = {"the", "a", "an", "is", "are", "of", "to", "in", "on", "for", "and", "or", "where", "who", "what", "we", "never"}

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
```

- [ ] **Step 4: Pass + commit**

```bash
git add steward/grounded.py tests/test_grounded.py
git commit -m "$(cat <<'EOF'
feat: filter allowlist hits and label grounded answers

EOF
)"
```

---

### Task 7: Memory wrapper (Cognee behind a seam)

**Files:**
- Create: `steward/memory.py`
- Test: `tests/test_memory.py`

**Interfaces:**
- Consumes: dataset name `steward`
- Produces: async `remember_text(text, *, dataset_name, external_metadata=None)`; async `recall(question, *, datasets, top_k=5) -> list[dict]`
- Tests mock `cognee` module; do not hit Qdrant

- [ ] **Step 1: Write failing tests with mock cognee**

```python
# tests/test_memory.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_remember_calls_cognee_without_session_id():
    with patch("steward.memory.cognee") as cognee:
        cognee.remember = AsyncMock(return_value=None)
        from steward.memory import remember_text
        await remember_text("hello", dataset_name="steward", external_metadata={"permalink": "p"})
        kwargs = cognee.remember.await_args.kwargs
        assert kwargs.get("dataset_name") == "steward"
        assert "session_id" not in kwargs

@pytest.mark.asyncio
async def test_recall_top_k_default():
    with patch("steward.memory.cognee") as cognee:
        cognee.recall = AsyncMock(return_value=[{"text": "x"}])
        from steward.memory import recall
        hits = await recall("q", datasets=["steward"])
        assert hits == [{"text": "x"}]
        assert cognee.recall.await_args.kwargs.get("top_k") == 5
```

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_memory.py -v`

- [ ] **Step 3: Implement wrapper**

Prefer `DataItem` when `external_metadata` is set (research). If import fails on the pin, fall back to embedding permalink in the text body only (design already requires both).

```python
# steward/memory.py
from __future__ import annotations
from typing import Any

import cognee

DATASET = "steward"

async def remember_text(
    text: str,
    *,
    dataset_name: str = DATASET,
    external_metadata: dict[str, Any] | None = None,
) -> None:
    data: Any = text
    if external_metadata is not None:
        try:
            from cognee.modules.data.models import DataItem  # adjust if pin path differs
            data = DataItem(data=text, external_metadata=external_metadata)
        except Exception:
            # still store; permalink must already be inside text
            data = text
    await cognee.remember(data, dataset_name=dataset_name)

async def recall(
    question: str,
    *,
    datasets: list[str] | None = None,
    top_k: int = 5,
) -> list[dict]:
    datasets = datasets or [DATASET]
    result = await cognee.recall(question, datasets=datasets, top_k=top_k)
    if result is None:
        return []
    if isinstance(result, list):
        return result
    return [{"text": str(result)}]
```

Adjust `DataItem` import path against the live pin during implementation (design Least confident #2). Keep tests green with the mock.

- [ ] **Step 4: Pass + commit**

```bash
git add steward/memory.py tests/test_memory.py
git commit -m "$(cat <<'EOF'
feat: wrap cognee remember and recall

EOF
)"
```

---

### Task 8: Event ingest skip rules

**Files:**
- Create: `steward/events.py`
- Test: `tests/test_events.py`

**Interfaces:**
- Consumes: Slack event dict, bot user id
- Produces: `should_ingest_message(event, bot_user_id) -> bool`; `format_channel_memory_text(event, permalink) -> str`

Skip when: subtype `bot_message`, empty text, user is this bot, text starts with `/`.

- [ ] **Step 1: Write failing tests**

```python
from steward.events import format_channel_memory_text, should_ingest_message

BOT = "UBOT"

def test_skip_bot_message():
    assert should_ingest_message({"subtype": "bot_message", "text": "x", "user": "U1"}, BOT) is False

def test_skip_empty():
    assert should_ingest_message({"text": "  ", "user": "U1"}, BOT) is False

def test_skip_self():
    assert should_ingest_message({"text": "hi", "user": BOT}, BOT) is False

def test_skip_slash_echo():
    assert should_ingest_message({"text": "/steward-ask hi", "user": "U1"}, BOT) is False

def test_accept_human():
    assert should_ingest_message({"text": "hello", "user": "U1", "channel": "C1", "ts": "1.2"}, BOT) is True

def test_format_includes_permalink():
    text = format_channel_memory_text(
        {"text": "hello", "user": "U1", "channel": "C1", "ts": "1.2"},
        "https://slack/p",
    )
    assert "https://slack/p" in text
    assert "C1" in text
    assert "hello" in text
```

- [ ] **Step 2–4: Implement, pass, commit**

```python
# steward/events.py
from __future__ import annotations

def should_ingest_message(event: dict, bot_user_id: str) -> bool:
    if event.get("subtype") == "bot_message":
        return False
    text = (event.get("text") or "").strip()
    if not text:
        return False
    if event.get("user") == bot_user_id:
        return False
    if text.startswith("/"):
        return False
    return True

def format_channel_memory_text(event: dict, permalink: str) -> str:
    return (
        f"[Channel Memory] channel={event.get('channel')} user={event.get('user')} "
        f"ts={event.get('ts')} permalink={permalink}\n{event.get('text')}"
    )
```

```bash
git add steward/events.py tests/test_events.py
git commit -m "$(cat <<'EOF'
feat: define Slack channel ingest skip rules

EOF
)"
```

---

### Task 9: GitHub issues/PR poll

**Files:**
- Create: `steward/github_ingest.py`
- Test: `tests/test_github_ingest.py`

**Interfaces:**
- Consumes: `repos: list[str]`, optional token, `since` ISO timestamp, httpx client
- Produces: `fetch_repo_issues(owner, repo, since, token=None) -> list[dict]`; `map_issue_to_memory(item, repo) -> {text, metadata, ledger_row}`; skips when HTTP fails (caller logs)

API: `GET /repos/{owner}/{repo}/issues?state=all&sort=updated&direction=desc&since=...&per_page=100`. PRs have `pull_request` key. Cite `html_url` only.

- [ ] **Step 1: Write failing tests with httpx mock**

```python
import httpx
import respx  # if avoiding new dep, use unittest.mock on httpx.AsyncClient.get instead
import pytest
from steward.github_ingest import map_issue_to_memory, parse_repos

def test_parse_repos_default():
    assert parse_repos(["topoteretes/cognee", "qdrant/qdrant"]) == [
        ("topoteretes", "cognee"),
        ("qdrant", "qdrant"),
    ]

def test_map_issue_vs_pr():
    issue = {
        "html_url": "https://github.com/topoteretes/cognee/issues/1",
        "number": 1,
        "title": "docs",
        "state": "open",
        "updated_at": "2026-08-14T10:00:00Z",
        "user": {"login": "alice"},
    }
    pr = {**issue, "html_url": "https://github.com/topoteretes/cognee/pull/2", "number": 2, "pull_request": {}}
    mi = map_issue_to_memory(issue, "topoteretes/cognee")
    mp = map_issue_to_memory(pr, "topoteretes/cognee")
    assert mi["ledger_row"]["kind"] == "issue"
    assert mp["ledger_row"]["kind"] == "pull_request"
    assert "html_url" in mi["text"] or mi["ledger_row"]["permalink"].startswith("https://github.com/")
    assert "api.github.com" not in mi["ledger_row"]["permalink"]
```

Prefer `unittest.mock` over adding `respx` (YAGNI). Add one async test that a 403 returns `[]` without raising.

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_github_ingest.py -v`

- [ ] **Step 3: Implement**

```python
# steward/github_ingest.py
from __future__ import annotations
import logging
from typing import Any
import httpx

log = logging.getLogger(__name__)

def parse_repos(repos: list[str]) -> list[tuple[str, str]]:
    out = []
    for r in repos:
        owner, name = r.split("/", 1)
        out.append((owner, name))
    return out

def map_issue_to_memory(item: dict[str, Any], repo: str) -> dict[str, Any]:
    kind = "pull_request" if "pull_request" in item else "issue"
    html_url = item["html_url"]
    login = (item.get("user") or {}).get("login")
    updated = item.get("updated_at")
    title = item.get("title")
    state = item.get("state")
    number = item.get("number")
    text = (
        f"[GitHub Memory] repo={repo} kind={kind} number={number} state={state} "
        f"login={login} updated_at={updated} html_url={html_url}\n{title}"
    )
    meta = {
        "html_url": html_url,
        "number": number,
        "title": title,
        "state": state,
        "login": login,
        "updated_at": updated,
        "repo": repo,
    }
    row = {
        "origin": "github",
        "channel_id": None,
        "repo": repo,
        "permalink": html_url,
        "text": f"{kind} #{number}: {title}",
        "occurred_at": updated,
        "updated_at": updated,
        "state": state,
        "user_id": None,
        "kind": kind,
    }
    return {"text": text, "metadata": meta, "ledger_row": row}

async def fetch_repo_issues(
    owner: str,
    repo: str,
    since: str,
    token: str | None = None,
    client: httpx.AsyncClient | None = None,
) -> list[dict]:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    url = f"https://api.github.com/repos/{owner}/{repo}/issues"
    params = {
        "state": "all",
        "sort": "updated",
        "direction": "desc",
        "since": since,
        "per_page": 100,
    }
    own = client is None
    client = client or httpx.AsyncClient(timeout=30.0)
    try:
        r = await client.get(url, headers=headers, params=params)
        if r.status_code in (401, 403, 404):
            log.warning("github skip %s/%s status=%s", owner, repo, r.status_code)
            return []
        if r.status_code == 403 and r.headers.get("X-RateLimit-Remaining") == "0":
            log.warning("github rate limit reset=%s", r.headers.get("X-RateLimit-Reset"))
            return []
        r.raise_for_status()
        items = r.json()
        if len(items) >= 100:
            log.warning("github cap 100 items for %s/%s", owner, repo)
        return items
    except httpx.HTTPError as e:
        log.warning("github error %s/%s: %s", owner, repo, e)
        return []
    finally:
        if own:
            await client.aclose()
```

- [ ] **Step 4: Pass + commit**

```bash
git add steward/github_ingest.py tests/test_github_ingest.py
git commit -m "$(cat <<'EOF'
feat: poll GitHub issues and PRs for memory

EOF
)"
```

---

### Task 10: Digest window + renderer (TLDR → Summary → Attention)

**Files:**
- Create: `steward/digest.py`
- Test: `tests/test_digest.py`

**Interfaces:**
- Consumes: ledger rows, window kind `daily|weekly`, tz name, allowlist, now datetime
- Produces: `window_bounds(kind, tz, now) -> (start, end)`; `render_digest(kind, rows, allowlist, channel_names=None) -> str`

Rules from design:
- Daily: today 00:00 TZ → now. Weekly: Monday 00:00 ISO week → now.
- Summary: Slack allowlist channel memory + remember facts by channel; GitHub one block per repo; issues/PRs only; no person merge; no seed docs.
- TLDR: up to 5 newest Summary bullets.
- Attention: open GitHub issues/PRs in window; else `_None in this window._`
- Empty Slack: `_No remembered channel activity in this window._`
- Caps: 20 bullets per Summary origin block, 40 Summary total; overflow line `N more in ledger, not shown.`
- Every bullet ends with permalink/`html_url`.

- [ ] **Step 1: Write failing tests with fixed TZ and fake ledger**

```python
from datetime import datetime
from zoneinfo import ZoneInfo
from steward.digest import render_digest, window_bounds

BERLIN = ZoneInfo("Europe/Berlin")

def test_daily_window():
    now = datetime(2026, 8, 14, 21, 30, tzinfo=BERLIN)
    start, end = window_bounds("daily", "Europe/Berlin", now)
    assert start == datetime(2026, 8, 14, 0, 0, tzinfo=BERLIN)
    assert end == now

def test_weekly_window_monday_start():
    now = datetime(2026, 8, 14, 21, 30, tzinfo=BERLIN)  # Friday
    start, end = window_bounds("weekly", "Europe/Berlin", now)
    assert start == datetime(2026, 8, 10, 0, 0, tzinfo=BERLIN)  # Monday
    assert end == now

def test_render_three_parts_and_no_person_merge():
    rows = [
        {
            "origin": "slack_channel",
            "channel_id": "C1",
            "repo": None,
            "permalink": "https://slack/p1",
            "text": "vectors in Qdrant Cloud",
            "occurred_at": "2026-08-14T10:00:00+02:00",
            "updated_at": None,
            "state": None,
            "user_id": "U1",
            "kind": "message",
        },
        {
            "origin": "github",
            "channel_id": None,
            "repo": "topoteretes/cognee",
            "permalink": "https://github.com/topoteretes/cognee/pull/9",
            "text": "PR opened: flash model",
            "occurred_at": "2026-08-14T11:00:00Z",
            "updated_at": "2026-08-14T11:00:00Z",
            "state": "open",
            "user_id": None,
            "kind": "pull_request",
        },
        {
            "origin": "slack_channel",
            "channel_id": "C9",
            "repo": None,
            "permalink": "https://slack/off",
            "text": "offlist",
            "occurred_at": "2026-08-14T12:00:00+02:00",
            "updated_at": None,
            "state": None,
            "user_id": "U2",
            "kind": "message",
        },
    ]
    body = render_digest(
        "daily",
        rows,
        allowlist=["C1"],
        title_day="Thu 14 Aug",
        channel_names={"C1": "steward"},
    )
    assert "*TLDR*" in body
    assert "*Summary*" in body
    assert "*Attention / action required*" in body
    assert "*Slack · #steward*" in body
    assert "*GitHub · topoteretes/cognee*" in body
    assert "offlist" not in body
    assert "U1" not in body or "<@U1>" in body  # no github login join required
    assert "https://github.com/topoteretes/cognee/pull/9" in body
```

Add tests for empty-window copy, TLDR cap 5, Attention open-only, bullet cap.

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_digest.py -v`

- [ ] **Step 3: Implement renderer** (keep pure functions; no LLM)

Implement `window_bounds` with `zoneinfo`. Filter rows by `occurred_at`/`updated_at` into `[start, end]`. Build Summary bullets, then TLDR from newest 5, then Attention from `origin==github` and `state==open`. Match shell from design (mrkdwn).

- [ ] **Step 4: Pass + commit**

```bash
git add steward/digest.py tests/test_digest.py
git commit -m "$(cat <<'EOF'
feat: render daily and weekly digests from ledger

EOF
)"
```

---

### Task 11: FastAPI app — commands + events (mocked Cognee)

**Files:**
- Create: `steward/app.py`
- Test: `tests/test_commands.py`

**Interfaces:**
- Consumes: Tasks 2–10
- Produces: FastAPI app with:
  - `POST /api/v1/slack/commands`
  - `POST /api/v1/slack/events`
- Flow: verify signature → allowlist check → ephemeral ack within 3s → background work → `response_url`

Commands: `/steward-ask`, `/steward-remember`, `/steward-digest daily|weekly`. Off-list → `REFUSE_TEXT`. Events: url_verification challenge; `message.channels` → remember + ledger when `should_ingest_message`.

- [ ] **Step 1: Write failing routing tests**

Use FastAPI `TestClient`. Mock `verify_slack_signature` True. Mock memory remember/recall. Assert:
1. Off-allowlist ask returns refuse and does not call recall.
2. On-allowlist remember calls remember + ledger append.
3. Digest bad arg returns usage hint.
4. Invalid signature → 401.
5. Url verification echoes challenge.

- [ ] **Step 2: Run to fail**

Run: `pytest tests/test_commands.py -v`

- [ ] **Step 3: Implement routes**

Skeleton:

```python
# steward/app.py
from fastapi import FastAPI, Request, BackgroundTasks, Response
from fastapi.responses import JSONResponse, PlainTextResponse

app = FastAPI(title="steward")

@app.post("/api/v1/slack/commands")
async def slack_commands(request: Request, background_tasks: BackgroundTasks):
    body = await request.body()
    # verify → parse form → allowlist → ack JSON or empty 200
    # schedule ask/remember/digest worker that posts to response_url
    ...

@app.post("/api/v1/slack/events")
async def slack_events(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    if payload.get("type") == "url_verification":
        return PlainTextResponse(payload["challenge"])
    # verify signature on raw body for event callbacks
    ...
```

Ack first after cheap allowlist check. Cognee/Qdrant failures after ack → ephemeral "Something went wrong" + log. No stack traces in Slack.

For digest slash: pull GitHub for window start, append new ledger rows, then `render_digest`.

- [ ] **Step 4: Pass + commit**

```bash
git add steward/app.py tests/test_commands.py
git commit -m "$(cat <<'EOF'
feat: add Slack commands and events FastAPI routes

EOF
)"
```

---

### Task 12: Seed docs + CLI

**Files:**
- Create: `steward/seed.py`
- Create: `steward/__main__.py`
- Create: `docs/seed/steward-overview.md`
- Test: extend `tests/test_commands.py` or `tests/test_seed.py` with mocked remember

**Interfaces:**
- Consumes: `docs/seed/*.md`
- Produces: `async seed_docs(path, dataset_name)` once; ledger origin `seed`; ask can quote filename

- [ ] **Step 1: Write one short seed file**

```markdown
# Steward overview

Steward stores vectors in Qdrant Cloud.
Steward uses Cognee remember and recall on dataset steward.
Steward digests use TLDR, Summary, and Attention.
```

- [ ] **Step 2: Test seed skips duplicate filenames already in ledger; remembers new files**

- [ ] **Step 3: Implement `python -m steward seed`**

```python
# steward/__main__.py
import asyncio
from steward.seed import seed_docs

if __name__ == "__main__":
    asyncio.run(seed_docs("docs/seed"))
```

- [ ] **Step 4: Commit**

```bash
git add steward/seed.py steward/__main__.py docs/seed/steward-overview.md tests/test_seed.py
git commit -m "$(cat <<'EOF'
feat: seed steward overview docs into memory

EOF
)"
```

---

### Task 13: Startup join-all public + GitHub warm pull + APScheduler

**Files:**
- Create: `steward/join_channels.py`
- Modify: `steward/app.py` lifespan
- Test: `tests/test_join_channels.py` (httpx mocked); scheduler unit: digest channel missing → skip cron post

**Interfaces:**
- Consumes: bot token, digest settings
- Produces: list+join public channels (skip archived; backoff on rate limit); startup GitHub pull `since=now-7d`; daily/weekly jobs posting via `chat.postMessage` to `STEWARD_DIGEST_CHANNEL` only if that id is on allowlist; idempotency files `.steward/last_daily_digest` / `.steward/last_weekly_digest`

- [ ] **Step 1: Failing tests for join skip-archived and digest-channel gate**

- [ ] **Step 2: Implement join + scheduler in lifespan**

```python
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler(timezone=settings.digest_tz)
    # add daily/weekly jobs
    scheduler.start()
    await join_public_channels(...)
    await github_warm_pull(...)
    yield
    scheduler.shutdown(wait=False)
```

Cron failure on `chat.postMessage`: log once, do not tight-loop retry. Slash digest still works.

- [ ] **Step 3: Pass + commit**

```bash
git add steward/join_channels.py steward/app.py tests/test_join_channels.py
git commit -m "$(cat <<'EOF'
feat: join public channels and schedule digests

EOF
)"
```

---

### Task 14: Slack manifest + operator runbook (laptop + ngrok)

**Files:**
- Create: `slack-manifest.json`
- Modify: `README.md` (run steps only; do not paste secrets)
- Create: `docs/runbook-hacknight.md` only if README would get too long; prefer README section

**Interfaces:**
- Consumes: none
- Produces: operator checklist for Friday demo

- [ ] **Step 1: Write Slack app manifest scopes/commands**

Scopes: `commands`, `chat:write`, `channels:read`, `channels:join`. Event: `message.channels`. Commands: `/steward-ask`, `/steward-remember`, `/steward-digest`.

Request URLs (placeholders):
- Commands: `https://<ngrok>/api/v1/slack/commands`
- Events: `https://<ngrok>/api/v1/slack/events`

- [ ] **Step 2: Document run order in README Status/Next**

1. Copy `.env.example` → `.env`; fill Slack, OpenRouter, Qdrant, allowlist + digest channel ids **before demo**.
2. `pip install` per Task 1.
3. `uvicorn steward.app:app --host 0.0.0.0 --port 8000`
4. `ngrok http 8000` → paste HTTPS into Slack app.
5. `python -m steward seed`
6. Live checklist from design Demo script.

- [ ] **Step 3: Commit**

```bash
git add slack-manifest.json README.md
git commit -m "$(cat <<'EOF'
docs: add Slack manifest and laptop ngrok runbook

EOF
)"
```

---

### Task 15: Full unit suite gate + live checklist (no secrets in git)

**Files:**
- Modify: none required if suite already covers design Testing section
- Optional: `docs/superpowers/plans/2026-08-14-steward-slice1-live-check.md` only if you need a checklist file; otherwise keep checklist in README

- [ ] **Step 1: Run full unit suite**

Run: `pytest -v`
Expected: all PASS. No live network.

- [ ] **Step 2: Operator live check (manual, after env filled)**

From design Demo script:

1. Laptop FastAPI up; ngrok matches Slack URLs.
2. Allowlist: `/steward-remember` fact about Qdrant Cloud.
3. Human message in allowlist channel.
4. `/steward-ask where are Steward's vectors stored?` → `SOURCED`
5. Ask about channel message or seed → `SOURCED`
6. Ask about recent Cognee/Qdrant GitHub activity → `SOURCED` + `html_url`
7. `/steward-digest daily` and `weekly` → TLDR, Summary (Slack then GitHub), Attention; no person merge
8. Unknown CEO question → `NOT DETERMINABLE`
9. Off-allowlist `/steward-ask` → refuse

- [ ] **Step 3: Commit any test fixes only (no `.env`, no `steward_api_key.txt`)**

```bash
git status
# ensure secrets untracked
pytest -v
git add tests/
git commit -m "$(cat <<'EOF'
test: close slice1 unit coverage gaps

EOF
)"
```

---

## Self-review (plan vs design)

| Design requirement | Task |
|---|---|
| Ask / remember / channel ingest / seed / labels | 6, 7, 8, 11, 12 |
| Allowlist gate + refuse | 4, 11 |
| GitHub issues+PRs two repos, poll, dedup, cap 100 | 9, 11, 13 |
| Digest TLDR→Summary→Attention, TZ Berlin, slash + cron | 10, 11, 13 |
| OpenRouter DeepSeek V4 Flash GA id | 1, 2 |
| Qdrant Cloud env + Cognee pin | 1, 7, Global Constraints |
| Laptop + ngrok | 14 |
| No Person Rollup | 10 tests assert no cross-link |
| No Linear | Global Constraints; no Linear files |
| Error handling (401, refuse, GitHub skip, ack-first) | 3, 9, 11, 13 |
| Unit tests without live APIs | all test tasks |

**Least confident for implementers (carry from design):**

1. `DataItem` import path on Cognee `@dev` may differ; fall back to text-only remember with permalink in body.
2. OpenRouter Flash id pinned to `openrouter/deepseek/deepseek-v4-flash-0731` (GA). Alternates: `openrouter/deepseek/deepseek-v4-flash` (0423), `openrouter/~deepseek/deepseek-v4-flash-latest` if LiteLLM accepts the `~` alias (unverified in Cognee).
3. Fastembed install on the demo laptop may fail; swap embedding env only.
4. Off-allowlist Channel Memory can crowd `top_k=5`; raise `top_k` before architecture change.

---

## Execution handoff

Plan complete and saved to `docs/superpowers/plans/2026-08-14-steward-slice1.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — fresh subagent per task, review between tasks  
2. **Inline Execution** — execute tasks in this session with executing-plans checkpoints  

Skim this plan, then say **build** (and pick 1 or 2) to start implementing. Do not implement until that word.
