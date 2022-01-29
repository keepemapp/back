from dataclasses import field
from typing import Optional

from pydantic.dataclasses import dataclass

from kpm.shared.domain import init_id, required_field
from kpm.shared.domain.commands import Command
from kpm.shared.domain.model import UserId


@dataclass(frozen=True)
class RegisterUser(Command):
    username: str = required_field()  # type: ignore
    password: str = required_field(repr=False)  # type: ignore
    email: str = required_field(repr=False)  # type: ignore
    user_id: Optional[str] = field(default_factory=lambda: init_id(UserId).id)
    public_name: Optional[str] = field(default=None, repr=False)
    referred_by: Optional[str] = field(default=None)


@dataclass(frozen=True)
class ActivateUser(Command):
    user_id: str = required_field()  # type: ignore


@dataclass(frozen=True)
class UpdateUser(Command):
    user_id: str = required_field()  # type: ignore
    public_name: Optional[str] = None

    def update_dict(self):
        return {"public_name": self.public_name}


@dataclass(frozen=True)
class UpdateUserPassword(Command):
    user_id: str = required_field()  # type: ignore
    old_password: str = required_field(repr=False)  # type: ignore
    new_password: str = required_field(repr=False)  # type: ignore


@dataclass(frozen=True)
class RequestKeep(Command):
    requester: str = required_field()  # type: ignore
    name_by_requester: Optional[str] = None
    requested: str = required_field()  # type: ignore


@dataclass(frozen=True)
class AcceptKeep(Command):
    """User ID of the user who accepts the keep"""

    by: str = required_field()  # type: ignore
    keep_id: str = required_field()  # type: ignore
    name_by_requested: Optional[str] = None


@dataclass(frozen=True)
class DeclineKeep(Command):
    """User ID of the user who declines the keep"""

    by: str = required_field()  # type: ignore
    keep_id: str = required_field()  # type: ignore
    reason: Optional[str] = field(default=None)
