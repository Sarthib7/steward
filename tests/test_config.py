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
    for k in ("STEWARD_DIGEST_TZ", "GITHUB_REPOS", "LLM_MODEL", "STEWARD_INGEST_CHANNELS"):
        monkeypatch.delenv(k, raising=False)

    s = load_settings()
    assert s.allowlist_channels == ["C1", "C2"]
    assert s.digest_channel == "C1"
    assert s.digest_tz == "Europe/Berlin"
    assert s.github_repos == ["topoteretes/cognee", "qdrant/qdrant"]
    assert s.llm_model == "openrouter/deepseek/deepseek-v4-flash-0731"
    assert s.dataset_name == "steward"
    assert s.ingest_channels == []
    assert s.memory_channels() == ["C1", "C2"]


def test_ingest_channels_union_into_memory_channels(monkeypatch):
    monkeypatch.setenv("SLACK_SIGNING_SECRET", "sig")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv("STEWARD_ALLOWLIST_CHANNELS", "C1")
    monkeypatch.setenv("STEWARD_INGEST_CHANNELS", "C9, C1")
    monkeypatch.setenv("STEWARD_DIGEST_CHANNEL", "C1")
    monkeypatch.setenv("LLM_API_KEY", "or-key")
    monkeypatch.setenv("VECTOR_DB_URL", "https://example.qdrant.io")
    monkeypatch.setenv("VECTOR_DB_KEY", "q-key")
    s = load_settings()
    assert s.ingest_channels == ["C9", "C1"]
    assert s.allowlist_channels == ["C1"]
    assert s.memory_channels() == ["C1", "C9"]
