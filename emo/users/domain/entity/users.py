from dataclasses import dataclass
from typing import Optional
import re

from emo.shared.domain import RootAggregate, UserId, init_id


@dataclass(frozen=True)
class User(RootAggregate):
    id: UserId
    username: str
    salt: str
    password_hash: str
    email: str
    disabled: Optional[bool] = False

    @staticmethod
    def _is_valid_email(email):
        regex = "^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,5}$"
        if not re.match(regex, email):
            raise ValueError("It's not an email address.")
        return email

    def __post_init__(self):
        super().__post_init__()
        if not self._validate_id_type(UserId):
            raise ValueError("ID is not of correct type")
        if not self._is_valid_email(self.email):
            raise ValueError("Email is not valid")
