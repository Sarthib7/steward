from __future__ import annotations

import os
from typing import Any

DATASET = "steward"

# Lazy import so unit tests can patch without installing cognee
_cognee = None
_adapter_registered = False


def ensure_qdrant_adapter() -> None:
    """Register the community Qdrant adapter before any Cognee call.

    VECTOR_DB_PROVIDER=qdrant is not enough. Importing register is not enough.
    Call register() in this process, then remember/recall.
    """
    global _adapter_registered
    if _adapter_registered:
        return
    if os.getenv("STEWARD_SKIP_STARTUP") == "1":
        return
    from cognee_community_vector_adapter_qdrant import register

    if callable(register):
        register()
    _adapter_registered = True


def _cognee_mod():
    global _cognee
    ensure_qdrant_adapter()
    if _cognee is None:
        try:
            import cognee as cognee_mod
        except ImportError as e:
            raise ImportError("cognee is not installed") from e
        _cognee = cognee_mod
    return _cognee


async def remember_text(
    text: str,
    *,
    dataset_name: str = DATASET,
    external_metadata: dict[str, Any] | None = None,
) -> None:
    cognee = _cognee_mod()
    data: Any = text
    if external_metadata is not None:
        try:
            from cognee.modules.data.models import DataItem

            data = DataItem(data=text, external_metadata=external_metadata)
        except Exception:
            data = text
    await cognee.remember(data, dataset_name=dataset_name)


async def recall(
    question: str,
    *,
    datasets: list[str] | None = None,
    top_k: int = 5,
) -> list[dict]:
    cognee = _cognee_mod()
    datasets = datasets or [DATASET]
    result = await cognee.recall(question, datasets=datasets, top_k=top_k)
    if result is None:
        return []
    if isinstance(result, list):
        return result
    return [{"text": str(result)}]
