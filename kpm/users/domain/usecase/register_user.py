import dataclasses
from dataclasses import dataclass
from typing import NoReturn

from kpm.shared.domain import init_id
from kpm.shared.domain.commands import CommandOld
from kpm.shared.domain.events import Event
from kpm.shared.domain.model import RootAggState, UserId
from kpm.shared.security import generate_salt, hash_password, salt_password
from kpm.users.domain.entity.user_repository import UserRepository
from kpm.users.domain.entity.users import User
from kpm.users.domain.usecase.exceptions import (
    EmailAlreadyExistsException,
    UsernameAlreadyExistsException,
)


@dataclass(frozen=True)
class UserRegistered(Event):
    eventType: str = "user_created"
    aggregate: User = None


class RegisterUser(CommandOld):
    _repository: UserRepository

    def __init__(
        self,
        username: str,
        password: str,
        email: str,
        *,
        repository: UserRepository,
    ):
        super().__init__(repository=repository)
        salt = generate_salt()
        self._entity = User(
            username=username,
            email=email,
            id=init_id(UserId),
            salt=salt,
            password_hash=hash_password(salt_password(password, salt)),
        )

        self._event = UserRegistered(
            aggregate_id=self._entity.id.id,
            aggregate=self._entity.erase_sensitive_data(),
        )

    def execute(self) -> NoReturn:
        if self._repository.empty():
            self._entity = dataclasses.replace(
                self._entity, state=RootAggState.ACTIVE, roles=["admin"]
            )
            self._event = dataclasses.replace(
                self._event, aggregate=self._entity
            )

        e = self._entity
        if self._repository.exists_email(e.email):
            raise EmailAlreadyExistsException()
        if self._repository.exists_username(e.username):
            raise UsernameAlreadyExistsException()
        self._repository.create(e)
