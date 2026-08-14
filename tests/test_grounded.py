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


def test_keeps_ingest_channel_memory_when_in_cite_list():
    hits = [
        {"origin": "slack_channel", "channel_id": "C9", "text": "vectors in qdrant", "permalink": "p9"},
        {"origin": "slack_channel", "channel_id": "C8", "text": "noise", "permalink": "p8"},
    ]
    kept = filter_hits_for_allowlist(hits, ["C1", "C9"])
    assert [h["channel_id"] for h in kept] == ["C9"]
