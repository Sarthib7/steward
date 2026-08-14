from datetime import datetime
from zoneinfo import ZoneInfo

from steward.digest import (
    is_digest_intent,
    parse_named_channel,
    render_digest,
    window_bounds,
)

BERLIN = ZoneInfo("Europe/Berlin")


def test_daily_window():
    now = datetime(2026, 8, 14, 21, 30, tzinfo=BERLIN)
    start, end = window_bounds("daily", "Europe/Berlin", now)
    assert start == datetime(2026, 8, 14, 0, 0, tzinfo=BERLIN)
    assert end == now


def test_weekly_window_monday_start():
    now = datetime(2026, 8, 14, 21, 30, tzinfo=BERLIN)
    start, end = window_bounds("weekly", "Europe/Berlin", now)
    assert start == datetime(2026, 8, 10, 0, 0, tzinfo=BERLIN)
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
    assert "https://github.com/topoteretes/cognee/pull/9" in body


def test_digest_intent_situation_phrases():
    assert is_digest_intent("whats going on in the #all-hacknight")
    assert is_digest_intent("what's going on in the <#C0BP8V9S0UC|all-hacknight>")
    assert is_digest_intent("<@U123> whats going on")
    assert is_digest_intent("catch me up on #all-hacknight")
    assert not is_digest_intent("where are vectors stored")
    assert not is_digest_intent("who is the CEO of a company we never mentioned?")


def test_parse_named_channel_hash_and_slack_mention():
    assert parse_named_channel("whats going on in the #all-hacknight") == (
        None,
        "all-hacknight",
    )
    assert parse_named_channel("in <#C0BP8V9S0UC|all-hacknight>") == (
        "C0BP8V9S0UC",
        "all-hacknight",
    )


def test_focus_channel_empty_slack_is_honest_not_not_determinable():
    rows = [
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
        }
    ]
    body = render_digest(
        "situation",
        rows,
        allowlist=["C1"],
        focus_channel_id="C0BP8V9S0UC",
        focus_channel_name="all-hacknight",
    )
    assert body.strip() != "NOT DETERMINABLE"
    assert "NOT DETERMINABLE" not in body
    assert "*TLDR*" in body
    assert "*Summary*" in body
    assert "*Attention / action required*" in body
    assert "No Channel Memory for #all-hacknight yet" in body
    assert "*GitHub · topoteretes/cognee*" in body
    assert "https://github.com/topoteretes/cognee/pull/9" in body
