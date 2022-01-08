from dataclasses import dataclass, field
from typing import Optional

from kpm.shared.domain import init_id, required_field
from kpm.shared.domain.commands import Command
from kpm.shared.domain.model import UserId


@dataclass(frozen=True)
class RegisterUser(Command):
    username: str = required_field()  # type: ignore
    password: str = required_field()  # type: ignore
    email: str = required_field()  # type: ignore
    user_id: Optional[str] = field(default_factory=lambda: init_id(UserId).id)


@dataclass(frozen=True)
class ActivateUser(Command):
    user_id: str = required_field()  # type: ignore


@dataclass(frozen=True)
class RequestKeep(Command):
    requester: str = required_field()  # type: ignore
    name_by_requester: str = None
    requested: str = required_field()  # type: ignore


@dataclass(frozen=True)
class AcceptKeep(Command):
    """User ID of the user who accepts the keep"""

    by: str = required_field()  # type: ignore
    keep_id: str = required_field()  # type: ignore
    name_by_requested: str = None


@dataclass(frozen=True)
class DeclineKeep(Command):
    """User ID of the user who declines the keep"""

    by: str = required_field()  # type: ignore
    keep_id: str = required_field()  # type: ignore
    reason: Optional[str] = field(default="")
