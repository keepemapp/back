from typing import NoReturn
from dataclasses import dataclass


from emo.users.domain.entity.users import User
from emo.users.domain.entity.user_repository import UserRepository
from emo.shared.domain.usecase import Command, Event, EventPublisher
from emo.shared.domain import UserId, init_id
from emo.shared.security import generate_salt, salt_password, hash_password


@dataclass(frozen=True)
class UserRegistered(Event):
    eventType: str = "user_created"


class RegisterUser(Command):
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

        self._event = UserRegistered(aggregate=self._entity.erase_sensitive_data())

    def execute(self) -> NoReturn:
        self._repository.create(self._entity)
        self._message_bus.publish(
            UserRegistered(aggregate=self._entity.erase_sensitive_data())
        )
