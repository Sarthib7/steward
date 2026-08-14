from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from steward.seed import seed_docs


@pytest.mark.asyncio
async def test_seed_skips_duplicates(tmp_path: Path):
    seed_dir = tmp_path / "seed"
    seed_dir.mkdir()
    (seed_dir / "steward-overview.md").write_text("vectors in Qdrant Cloud\n")
    ledger = tmp_path / "ingest.jsonl"
    with (
        patch("steward.seed.ensure_qdrant_adapter"),
        patch("steward.seed.remember_text", new_callable=AsyncMock) as rem,
    ):
        n1 = await seed_docs(str(seed_dir), ledger_path=str(ledger))
        n2 = await seed_docs(str(seed_dir), ledger_path=str(ledger))
    assert n1 == 1
    assert n2 == 0
    assert rem.await_count == 1
