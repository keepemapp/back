from typing import List, Optional

from kpm.shared.domain.model import UserId
from kpm.shared.service_layer.message_bus import MessageBus
from kpm.users.domain.model import User


def all_users(bus: MessageBus) -> List[User]:
    with bus.uows.get(User) as uow:
        return [u.erase_sensitive_data() for u in uow.repo.all()]


def by_id(user_id: str, bus: MessageBus) -> Optional[User]:
    with bus.uows.get(User) as uow:
        user = uow.repo.get(UserId(user_id))
    if user:
        return user.erase_sensitive_data()
    else:
        return None


def credentials_email(email: str, bus: MessageBus) -> User:
    with bus.uows.get(User) as uow:
        user = next(
            (u for u in uow.repo.all() if u.email.lower() == email.lower()),
            None,
        )
    return user


def credentials_id(user_id: str, bus: MessageBus) -> User:
    with bus.uows.get(User) as uow:
        return uow.repo.get(UserId(user_id))
