from dataclasses import field
from typing import List, Optional

from pydantic.dataclasses import dataclass

from kpm.shared.domain import DomainId, init_id, required_field
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
class RemoveUser(Command):
    user_id: str = required_field()  # type: ignore
    reason: str = required_field()  # type: ignore
    deleted_by: str = required_field()  # type: ignore


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
    id: Optional[str] = field(default_factory=lambda: init_id(DomainId).id)


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


@dataclass(frozen=True)
class LoginUser(Command):
    email: Optional[str] = None  # type: ignore
    user_id: Optional[str] = None  # type: ignore
    password: str = required_field(repr=False)  # type: ignore
    device_id: Optional[str] = None  # type: ignore
    scopes: List[str] = field(default_factory=list)  # type: ignore
    id: Optional[str] = field(default_factory=lambda: init_id(DomainId).id)

    def __post_init__(self):
        assert self.email or self.user_id


@dataclass(frozen=True)
class RemoveSession(Command):
    token: str = required_field()  # type: ignore
    removed_by: str = required_field()  # type: ignore


@dataclass(frozen=True)
class AddUserReminder(Command):
    user_id: str = required_field()  # type: ignore
    title: str = required_field()  # type: ignore
    time: int = required_field()  # type: ignore
    frequency: int = field(default=0)
    related_user: Optional[str] = field(default=None)  # type: ignore


@dataclass(frozen=True)
class RemoveUserReminder(Command):
    user_id: str = required_field()  # type: ignore
    title: str = required_field()  # type: ignore
    time: int = required_field()  # type: ignore