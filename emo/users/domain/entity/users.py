from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass
from typing import Optional

from emo.shared.domain import RootAggregate, UserId


@dataclass(frozen=True)
class User(RootAggregate):
    id: UserId
    username: str
    salt: Optional[str]
    password_hash: Optional[str]
    email: str
    disabled: Optional[bool] = False

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        regex = r"^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,5}$"
        return True if re.match(regex, email) else False

    def __post_init__(self):
        super().__post_init__()
        if not self._validate_id_type(UserId):
            raise ValueError("ID is not of correct type")
        if not self._is_valid_email(self.email):
            raise ValueError("Email is not valid")

    def disable(self) -> User:
        return dataclasses.replace(self, disabled=True)

    def erase_sensitive_data(self) -> User:
        return dataclasses.replace(self, salt=None, password_hash=None)

    def change_password_hash(self, new_password_hash):
        return dataclasses.replace(self, password_hash=new_password_hash)
