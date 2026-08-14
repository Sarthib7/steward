from steward.allowlist import REFUSE_TEXT, is_allowed


def test_on_list():
    assert is_allowed("C1", ["C1", "C2"]) is True


def test_off_list():
    assert is_allowed("C9", ["C1", "C2"]) is False


def test_refuse_copy():
    assert REFUSE_TEXT == "Steward isn't enabled here"
