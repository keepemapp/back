from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass
from typing import Optional

from emo.shared.domain import RootAggregate, UserId

INVALID_USERNAME = (
    "Username is not valid. It can contain letters, "
    "numbers and underscores and have between "
    "2 and 15 characters."
)
INVALID_EMAIL = "Email is not valid"
INVALID_ID = "ID is not of correct type. It needs to be UserId"


@dataclass(frozen=True)
class User(RootAggregate):
    id: UserId
    username: str
    salt: Optional[str]
    password_hash: Optional[str]
    email: str
    disabled: Optional[bool] = False

    @staticmethod
    def _email_is_valid(email: str) -> bool:
        regex = r"^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,5}$"
        return True if re.match(regex, email) else False

    @staticmethod
    def _name_is_valid(name: str) -> bool:
        regex = r"^[a-z_0-9]{2,15}$"
        return True if re.match(regex, name) else False

    def __post_init__(self):
        super().__post_init__()
        if not self._validate_id_type(UserId):
            raise ValueError(INVALID_ID)
        if not self._name_is_valid(self.username):
            raise ValueError(INVALID_USERNAME)
        if not self._email_is_valid(self.email):
            raise ValueError(INVALID_EMAIL)

    def disable(self) -> User:
        return dataclasses.replace(self, disabled=True)

    def erase_sensitive_data(self) -> User:
        return dataclasses.replace(self, salt=None, password_hash=None)

    def change_password_hash(self, new_password_hash):
        return dataclasses.replace(self, password_hash=new_password_hash)
