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
