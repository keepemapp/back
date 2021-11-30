from datetime import datetime, timezone


def to_millis(dt: datetime) -> int:
    return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)


def current_utc() -> datetime:
    return datetime.now(timezone.utc)


def current_utc_millis() -> int:
    # This is preferred over .utcnow() see
    # https://docs.python.org/3/library/datetime.html#datetime.datetime.utcnow
    return to_millis(current_utc())


def utc_from_timestamp(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp / 1000.0, timezone.utc)
