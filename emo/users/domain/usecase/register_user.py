from dataclasses import dataclass
from typing import NoReturn

from emo.shared.domain import Event, UserId, init_id
from emo.shared.domain.usecase import CommandOld, EventPublisher
from emo.shared.security import generate_salt, hash_password, salt_password
from emo.users.domain.entity.user_repository import UserRepository
from emo.users.domain.entity.users import User
from emo.users.domain.usecase.exceptions import (
    EmailAlreadyExistsException, UsernameAlreadyExistsException)


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
        message_bus: EventPublisher
    ):
        super().__init__(repository=repository, message_bus=message_bus)
        salt = generate_salt()
        self._entity = User(
            username=username,
            email=email,
            id=init_id(UserId),
            salt=salt,
            disabled=False,
            password_hash=hash_password(salt_password(password, salt)),
        )

        self._event = UserRegistered(
            aggregate_id=self._entity.id.id,
            aggregate=self._entity.erase_sensitive_data(),
        )

    def execute(self) -> NoReturn:
        e = self._entity
        if self._repository.exists_email(e.email):
            raise EmailAlreadyExistsException()
        if self._repository.exists_username(e.username):
            raise UsernameAlreadyExistsException()
        self._repository.create(e)
        self._message_bus.publish(self._event)
