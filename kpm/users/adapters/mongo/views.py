from dataclasses import asdict
from typing import Dict, List, Optional

import flatdict

from kpm.shared.adapters.mongo import mongo_client
from kpm.shared.domain.model import VISIBLE_STATES, UserId
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


def users_public_info(users: List[str], bus: MessageBus) -> List[Dict]:
    filter = {"_id": {"$in": users}}
    fields = {
        "_id": 0,
        "id": "$_id",
        "public_name": 1,
        "referral_code": 1,
        "email": 1,
    }
    with mongo_client() as client:
        col = client.users.users
        res = col.aggregate(
            [
                {"$match": filter},
                {"$project": fields},
            ]
        )
        results = list(res)
    return results


def id_from_referral(referral_code: str, bus: MessageBus) -> Optional[str]:
    with mongo_client() as client:
        col = client["users"].users
        res = col.find_one(
            filter={"referral_code": referral_code}, projection=["_id"]
        )

    return res.get("_id", None) if res else None


def id_from_email(email: str, bus: MessageBus) -> Optional[str]:
    with mongo_client() as client:
        col = client["users"].users
        res = col.find_one(filter={"email": email.lower()}, projection=["_id"])

    return res.get("_id", None) if res else None


def credentials_email(email: str, password: str, bus: MessageBus) -> User:
    user = None
    with bus.uows.get(User) as uow:
        user: User = uow.repo.by_email(email.lower().strip())
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
        keeps = repo.all(user=UserId(user_id))
    if state:
        keeps = [k for k in keeps if k.state.value == state.lower()]
    else:
        keeps = [k for k in keeps if k.state in VISIBLE_STATES]
    if order_by:
        is_reverse = order == "desc"
        keeps.sort(reverse=is_reverse, key=lambda a: getattr(a, order_by))
    return [keep_to_flat_dict(k) for k in keeps]
