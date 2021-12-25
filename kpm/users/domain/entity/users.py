from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass, field
from typing import List

from kpm.shared.domain import required_field
from kpm.shared.domain.model import RootAggregate, RootAggState, UserId

INVALID_USERNAME = (
    "Username is not valid. It can contain letters, "
    "numbers and underscores and have between "
    "2 and 15 characters."
)
INVALID_EMAIL = "Email is not valid"


@dataclass
class User(RootAggregate):
    id: UserId = required_field()
    username: str = required_field()
    salt: str = ""
    password_hash: str = ""
    email: str = required_field()
    state: RootAggState = field(default=RootAggState.PENDING_VALIDATION)
    roles: List[str] = field(default_factory=lambda: ["user"])

    @staticmethod
    def _email_is_valid(email: str) -> bool:
        regex = r"^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,5}$"
        return True if re.match(regex, email) else False

    @staticmethod
    def _name_is_valid(name: str) -> bool:
        regex = r"^[a-z_0-9]{2,15}$"
        return True if re.match(regex, name) else False

    def __post_init__(self):
        self._id_type_is_valid(UserId)
        if not self._name_is_valid(self.username):
            raise ValueError(INVALID_USERNAME)
        if not self._email_is_valid(self.email):
            raise ValueError(INVALID_EMAIL)

    def activate(self) -> User:
        return dataclasses.replace(self, state=RootAggState.ACTIVE)

    def disable(self) -> User:
        return dataclasses.replace(self, state=RootAggState.INACTIVE)

    def is_disabled(self) -> bool:
        return self.state not in [RootAggState.ACTIVE]

    def is_pending_validation(self):
        return self.state in [RootAggState.PENDING_VALIDATION]

    def erase_sensitive_data(self) -> User:
        return dataclasses.replace(self, salt=None, password_hash=None)

    def change_password_hash(self, new_password_hash):
        return dataclasses.replace(self, password_hash=new_password_hash)
