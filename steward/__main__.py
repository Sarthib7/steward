import asyncio

from dotenv import load_dotenv

from steward.memory import ensure_qdrant_adapter
from steward.seed import seed_docs


if __name__ == "__main__":
    load_dotenv()
    ensure_qdrant_adapter()
    asyncio.run(seed_docs("docs/seed"))
