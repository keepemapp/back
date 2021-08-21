from typing import NoReturn
from dataclasses import dataclass


from emo.users.domain.entity.users import User
from emo.users.domain.entity.user_repository import UserRepository
from emo.shared.security import salt_password, hash_password, verify_password
from emo.shared.domain import UserId
from emo.shared.domain.usecase import Command, Event, EventPublisher
from emo.users.domain.usecase.exceptions import MissmatchPasswordException


@dataclass(frozen=True)
class UserPasswordChanged(Event):
    eventType: str = "user_password_changed"


class ChangeUserPassword(Command):
    def __init__(
        self,
        *,
        user_id: UserId,
        old_password: str,
        new_password: str,
        repository: UserRepository,
        message_bus: EventPublisher,
    ):
        super().__init__(repository=repository, message_bus=message_bus)
        self.uid = user_id
        self.old = old_password
        self.new = new_password
        self._event = UserPasswordChanged(aggregate=user_id)

    def execute(self) -> NoReturn:
        u = self._repository.get(self.uid)

        if not verify_password(salt_password(self.old, u.salt), u.password_hash):
            raise MissmatchPasswordException()

        new = hash_password(salt_password(self.new, u.salt))
        self._repository.update(u.change_password_hash(new))
        self._message_bus.publish(self._event)
