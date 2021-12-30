from dataclasses import dataclass, field
from typing import Optional

from kpm.shared.domain import init_id
from kpm.shared.domain.commands import Command
from kpm.shared.domain.model import UserId


@dataclass(frozen=True)
class RegisterUser(Command):
    username: str
    password: str
    email: str
    user_id: Optional[str] = field(default_factory=lambda: init_id(UserId).id)


@dataclass(frozen=True)
class ActivateUser(Command):
    user_id: str
