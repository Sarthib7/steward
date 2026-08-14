REFUSE_TEXT = "Steward isn't enabled here"


def is_allowed(channel_id: str | None, allowlist: list[str]) -> bool:
    if not channel_id:
        return False
    return channel_id in set(allowlist)
