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


def test_skip_off_ingest_list():
    ev = {"text": "hello", "user": "U1", "channel": "C9", "ts": "1.2"}
    assert should_ingest_message(ev, BOT, ingest_channels=["C1"]) is False


def test_accept_on_ingest_list():
    ev = {"text": "hello", "user": "U1", "channel": "C9", "ts": "1.2"}
    assert should_ingest_message(ev, BOT, ingest_channels=["C9"]) is True


def test_ingest_list_none_keeps_old_behavior():
    ev = {"text": "hello", "user": "U1", "channel": "C9", "ts": "1.2"}
    assert should_ingest_message(ev, BOT) is True
