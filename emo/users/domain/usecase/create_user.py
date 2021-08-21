from typing import NoReturn
from dataclasses import dataclass


from emo.users.domain.entity.users import User
from emo.users.domain.entity.user_repository import UserRepository
from emo.shared.domain.usecase import Command, Event, EventPublisher
from emo.shared.domain import UserId, init_id
from emo.shared.security import generate_salt, salt_password, get_password_hash


@dataclass(frozen=True)
class UserCreated(Event):
    eventType: str = "user_created"


class CreateUser(Command):

    def __init__(self, username: str, password: str, email: str, *, repository: UserRepository,
                 message_bus: EventPublisher):
        super().__init__(repository=repository, message_bus=message_bus)
        salt = generate_salt()
        self._entity = User(
            username=username,
            email=email,
            id=init_id(UserId),
            salt=salt,
            disabled=False,
            password_hash=get_password_hash(salt_password(password, salt))
        )

        self._event = UserCreated(aggregate=self._entity.erase_sensitive_data())

    def execute(self) -> NoReturn:
        self._repository.create(self._entity)
        self._message_bus.publish(self._event)

