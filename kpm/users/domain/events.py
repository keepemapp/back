from dataclasses import field
from typing import Optional

from pydantic.dataclasses import dataclass

from kpm.shared.domain import required_field
from kpm.shared.domain.events import Event


@dataclass(frozen=True)
class UserRegistered(Event):
    eventType: str = "user_registered"
    username: str = required_field()  # type: ignore
    email: str = required_field()  # type: ignore
    referred_by: Optional[str] = field(default=None)


@dataclass(frozen=True)
class UserActivated(Event):
    eventType: str = "user_activated"


@dataclass(frozen=True)
class UserRemoved(Event):
    eventType: str = "user_removed"
    by: str = required_field()  # type: ignore
    reason: str = required_field()  # type: ignore


@dataclass(frozen=True)
class KeepRequested(Event):
    eventType: str = "keep_requested"
    requester: str = required_field()  # type: ignore
    requested: str = required_field()  # type: ignore


@dataclass(frozen=True)
class KeepAccepted(Event):
    eventType: str = "keep_accepted"
    requester: str = required_field()  # type: ignore
    requested: str = required_field()  # type: ignore


@dataclass(frozen=True)
class KeepDeclined(Event):
    eventType: str = "keep_declined"
    was_accepted: bool = required_field()  # type: ignore
    requester: str = required_field()  # type: ignore
    requested: str = required_field()  # type: ignore


@dataclass(frozen=True)
class UserReminderAdded(Event):
    eventType: str = "reminder_added"
    title: str = required_field()  # type: ignore
    time: int = required_field()  # type: ignore
    frequency: int = field(default=0)
    related_user: Optional[str] = field(default=None)  # type: ignore


@dataclass(frozen=True)
class UserReminderRemoved(Event):
    eventType: str = "reminder_removed"
    title: str = required_field()  # type: ignore
    time: int = required_field()  # type: ignore