from dataclasses import dataclass, field
from typing import Optional

from kpm.shared.domain import init_id, required_field
from kpm.shared.domain.commands import Command
from kpm.shared.domain.model import UserId


@dataclass(frozen=True)
class RegisterUser(Command):
    username: str = required_field()
    password: str = required_field()
    email: str = required_field()
    user_id: Optional[str] = field(default_factory=lambda: init_id(UserId).id)


@dataclass(frozen=True)
class ActivateUser(Command):
    user_id: str = required_field()


@dataclass(frozen=True)
class RequestKeep(Command):
    requester: str = required_field()
    name_by_requester: str = required_field()
    requested: str = required_field()


@dataclass(frozen=True)
class AcceptKeep(Command):
    keep_id: str = required_field()
    name_by_requested: str = required_field()


@dataclass(frozen=True)
class DeclineKeep(Command):
    keep_id: str = required_field()
    """User ID of the user who declines the keep"""
    by: str = required_field()
    reason: Optional[str] = field(default="")
