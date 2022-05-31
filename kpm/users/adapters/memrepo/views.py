from dataclasses import asdict
from typing import Dict, List, Optional

import flatdict

from kpm.shared.domain.model import RootAggState, UserId, VISIBLE_STATES
from kpm.shared.service_layer.message_bus import MessageBus
from kpm.users.domain.model import Keep, User
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


def users_public_info(users: List[str], bus: MessageBus) -> List[Dict]:
    with bus.uows.get(User) as uow:
        all_u = uow.repo.all()
        results = [
            {
                "id": u.id.id,
                "email": u.email,
                "public_name": u.public_name,
                "referral_code": u.referral_code,
            }
            for u in all_u
            if u.id.id in users
        ]
    return results


def id_from_referral(referral_code: str, bus: MessageBus) -> Optional[str]:
    with bus.uows.get(User) as uow:
        user = next(
            (u for u in uow.repo.all() if u.referral_code == referral_code),
            None,
        )
    return user.id.id if user else None


def id_from_email(email: str, bus: MessageBus) -> Optional[str]:
    with bus.uows.get(User) as uow:
        user = next(
            (u for u in uow.repo.all() if u.email == email.lower()),
            None,
        )
    return user.id.id if user else None


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
    else:
        keeps = [k for k in keeps if k.state in VISIBLE_STATES]
    if order_by:
        is_reverse = order == "desc"
        keeps.sort(reverse=is_reverse, key=lambda a: getattr(a, order_by))
    return [keep_to_flat_dict(k) for k in keeps]


def all_keeps(
    bus: MessageBus,
    order_by: str = None,
    order: str = "asc",
):
    with bus.uows.get(Keep) as uow:
        repo: KeepRepository = uow.repo
        keeps = repo.all()
    if order_by:
        is_reverse = order == "desc"
        keeps.sort(reverse=is_reverse, key=lambda a: getattr(a, order_by))
    return [keep_to_flat_dict(k) for k in keeps]


def pending_keeps(user_id: str, bus=None) -> int:
    uid = UserId(user_id)
    with bus.uows.get(Keep) as uow:
        repo: KeepRepository = uow.repo
        keeps = repo.all(uid)

    def pending_filter(k: Keep):
        return k.state == RootAggState.PENDING and k.requested == uid

    num_pending = len(list(filter(pending_filter, keeps)))
    return num_pending
