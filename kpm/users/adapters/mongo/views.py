from dataclasses import asdict
from typing import Dict, List, Optional, Union

import flatdict

from kpm.shared.adapters.mongo import mongo_client
from kpm.shared.domain.model import RootAggState, UserId, VISIBLE_STATES
from kpm.shared.entrypoints.auth_jwt import RefreshToken
from kpm.shared.service_layer.message_bus import MessageBus
from kpm.users.domain.model import (
    InvalidSession,
    Keep,
    Reminder, Session,
    User,
)
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
    with bus.uows.get(User) as uow:
        db = uow.repo.db
    with mongo_client() as client:
        col = client[db].users
        res = col.aggregate(
            [
                {"$match": filter},
                {"$project": fields},
            ]
        )
        results = list(res)
    return results


def reminder_to_flat_dict(r: Union[Reminder, Dict]):
    r = asdict(r) if isinstance(r, Reminder) else r
    d = dict(flatdict.FlatDict(r, delimiter="_"))
    if "related_user_id" in d:
        d["related_user"] = d.pop("related_user_id")
    return d


def get_user_reminders(user_id: str, bus: MessageBus) -> List[Dict]:
    with bus.uows.get(User) as uow:
        db = uow.repo.db
    with mongo_client() as client:
        col = client[db].users
        res = col.find_one({"_id": user_id}, projection=["reminders"])
    cleaned = [reminder_to_flat_dict(r) for r in res.get("reminders", [])]
    return cleaned


def id_from_referral(referral_code: str, bus: MessageBus) -> Optional[str]:
    with bus.uows.get(User) as uow:
        db = uow.repo.db
    with mongo_client() as client:
        col = client[db].users
        res = col.find_one(
            filter={"referral_code": referral_code}, projection=["_id"]
        )

    return res.get("_id", None) if res else None


def id_from_email(email: str, bus: MessageBus) -> Optional[str]:
    with bus.uows.get(User) as uow:
        db = uow.repo.db
    with mongo_client() as client:
        col = client[db].users
        res = col.find_one(filter={"email": email.lower()}, projection=["_id"])

    return res.get("_id", None) if res else None


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
    with bus.uows.get(User) as uow:
        db = uow.repo.db
    with mongo_client() as client:
        col = client[db].keeps
        filter = {
            "requested": user_id,
            "state": RootAggState.PENDING.value,
        }
        num_pending = col.count_documents(filter)
    return num_pending


def get_active_refresh_token(
    bus: MessageBus, session_id: str = None, token: str = None
) -> RefreshToken:
    with bus.uows.get(Session) as uow:
        if session_id:
            sessions = uow.repo.get(sid=session_id)
        else:
            sessions = uow.repo.get(token=token)
        for session in sessions:
            if session.is_active():
                return session.refresh_token
        # All other cases
        raise InvalidSession()
