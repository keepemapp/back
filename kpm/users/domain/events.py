from dataclasses import dataclass

from kpm.shared.domain import required_field
from kpm.shared.domain.events import Event


@dataclass(frozen=True)
class UserRegistered(Event):
    eventType: str = "user_registered"
    username: str = required_field()
    email: str = required_field()


@dataclass(frozen=True)
class UserActivated(Event):
    eventType: str = "user_activated"


@dataclass(frozen=True)
class KeepRequested(Event):
    eventType: str = "keep_requested"
    requester: str = required_field()
    requested: str = required_field()


@dataclass(frozen=True)
class KeepAccepted(Event):
    eventType: str = "keep_accepted"
    requester: str = required_field()
    requested: str = required_field()


@dataclass(frozen=True)
class KeepDeclined(Event):
    eventType: str = "keep_declined"
    was_accepted: bool = required_field()
    requester: str = required_field()
    requested: str = required_field()
