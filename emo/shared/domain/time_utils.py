from datetime import datetime, timezone


def current_utc_timestamp() -> int:
    # This is preferred over .utcnow() see
    # https://docs.python.org/3/library/datetime.html#datetime.datetime.utcnow
    return int(datetime.now(timezone.utc).timestamp())


def utc_from_timestamp(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp, timezone.utc)
