from datetime import datetime, timedelta, timezone


def to_millis(dt: datetime) -> int:
    return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)


def to_secs(value: datetime) -> int:
    if not isinstance(value, datetime):
        raise TypeError("a datetime is required")
    return int(value.replace(tzinfo=timezone.utc).timestamp())


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def now_utc_sec() -> int:
    return to_secs(now_utc())


def now_utc_millis() -> int:
    # This is preferred over .utcnow() see
    # https://docs.python.org/3/library/datetime.html#datetime.datetime.utcnow
    return to_millis(now_utc())


def utc_from_timestamp(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp / 1000.0, timezone.utc)


def from_now_ms(hours: int = 0, days: int = 0, months: int = 0,
                years: int = 0):
    """Returns the future milliseconds after adding the time delta"""
    total_hours = hours + 24 * (days + 30 * (months + 12 * years))
    delta_ms = timedelta(hours=total_hours).total_seconds() * 1000
    return now_utc_millis() + delta_ms
