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
    ingest_channels: list[str]
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


    def memory_channels(self) -> list[str]:
        out: list[str] = []
        for cid in (*self.allowlist_channels, *self.ingest_channels):
            if cid not in out:
                out.append(cid)
        return out


def _csv(name: str, default: str = "") -> list[str]:
    raw = os.getenv(name, default)
    return [p.strip() for p in raw.split(",") if p.strip()]


def load_settings() -> Settings:
    return Settings(
        slack_signing_secret=os.environ["SLACK_SIGNING_SECRET"],
        slack_bot_token=os.environ["SLACK_BOT_TOKEN"],
        allowlist_channels=_csv("STEWARD_ALLOWLIST_CHANNELS"),
        ingest_channels=_csv("STEWARD_INGEST_CHANNELS"),
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
