from dataclasses import asdict
from typing import List, Optional

import flatdict

from kpm.shared.domain.model import UserId
from kpm.shared.service_layer.message_bus import MessageBus
from kpm.users.domain.model import Keep, User, UserNotFound
from kpm.users.domain.repositories import KeepRepository


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


def credentials_email(email: str, password: str, bus: MessageBus) -> User:
    def is_email_equals(email1: str, email2: str):
        if "@gmail" in email1:
            return (
                email1.replace(".", "").lower()
                == email2.replace(".", "").lower()
            )
        else:
            return email1.lower() == email2.lower()

    with bus.uows.get(User) as uow:
        user: User = next(
            (u for u in uow.repo.all() if is_email_equals(u.email, email)),
            None,
        )
    if not user:
        raise UserNotFound()
    user.validate_password(password)
    return user


def credentials_id(user_id: str, password: str, bus: MessageBus) -> User:
    with bus.uows.get(User) as uow:
        user = uow.repo.get(UserId(user_id))
    if not user:
        raise UserNotFound()
    user.validate_password(password)
    return user


def keep_to_flat_dict(k: Keep):
    d = dict(flatdict.FlatDict(asdict(k), delimiter="_"))
    d["id"] = d.pop("id_id")
    d["requested"] = d.pop("requested_id")
    d["requester"] = d.pop("requester_id")
    d["state"] = d.pop("state").value
    d["modified_ts"] = k.last_modified()
    del d["events"]
    return d


def user_keeps(
    bus: MessageBus,
    user_id: str = None,
    order_by: str = None,
    order: str = "asc",
    state: str = None,
):
    with bus.uows.get(Keep) as uow:
        repo: KeepRepository = uow.repo
        keeps = repo.all(UserId(user_id))
    if state:
        keeps = [k for k in keeps if k.state.value == state.lower()]
    if order_by:
        is_reverse = order == "desc"
        keeps.sort(reverse=is_reverse, key=lambda a: getattr(a, order_by))
    return [keep_to_flat_dict(k) for k in keeps]
