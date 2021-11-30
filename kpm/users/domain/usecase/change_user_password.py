from dataclasses import dataclass
from typing import NoReturn

from kpm.shared.domain import Event, UserId
from kpm.shared.domain.usecase import CommandOld
from kpm.shared.security import hash_password, salt_password, verify_password
from kpm.users.domain.entity.user_repository import UserRepository
from kpm.users.domain.usecase.exceptions import MissmatchPasswordException


@dataclass(frozen=True)
class UserPasswordChanged(Event):
    eventType: str = "user_password_changed"


class ChangeUserPassword(CommandOld):
    def __init__(
        self,
        *,
        user_id: UserId,
        old_password: str,
        new_password: str,
        repository: UserRepository,
    ):
        super().__init__(repository=repository)
        self.uid = user_id
        self.old = old_password
        self.new = new_password
        self._event = UserPasswordChanged(aggregate_id=user_id)

    def execute(self) -> NoReturn:
        u = self._repository.get(self.uid)

        if not verify_password(
            salt_password(self.old, u.salt), u.password_hash
        ):
            raise MissmatchPasswordException()

        new = hash_password(salt_password(self.new, u.salt))
        self._repository.update(u.change_password_hash(new))
