from dataclasses import dataclass

from kpm.shared.domain import required_field
from kpm.shared.domain.events import Event


@dataclass(frozen=True)
class UserRegistered(Event):
    eventType: str = "user_registered"
    username: str = required_field()
    email: str = required_field()
