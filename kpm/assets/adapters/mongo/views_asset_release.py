from dataclasses import asdict
from typing import Dict, List, Optional

import flatdict

import kpm.assets.domain.model as model
from kpm.assets.adapters.mongo.repository import AssetReleaseMongoRepo
from kpm.assets.domain.repositories import AssetReleaseRepository
from kpm.shared.adapters.mongo import mongo_client
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import RootAggState, UserId
from kpm.shared.domain.time_utils import now_utc_millis
from kpm.shared.log import logger
from kpm.shared.service_layer.message_bus import MessageBus
from kpm.shared.service_layer.unit_of_work import AbstractUnitOfWork


def to_flat_dict(a: model.AssetRelease):
    if not a:
        return None
    d = dict(flatdict.FlatDict(asdict(a), delimiter="_"))
    d["id"] = d.pop("id_id")
    d["owner"] = d.pop("owner_id")
    d["receivers"] = [id["id"] for id in d.pop("receivers")]
    d["assets"] = [id["id"] for id in d.pop("assets")]
    del d["events"]
    d.pop("conditions")
    d["conditions"] = {}
    d["state"] = d["state"].value
    for c in a.conditions:
        if isinstance(c, model.TrueCondition):
            d["conditions"]["immediate"] = True
        elif isinstance(c, model.TimeCondition):
            d["conditions"]["release_time"] = c.release_ts
        elif isinstance(c, model.GeographicalCondition):
            d["conditions"]["location"] = c.location
    d["modified_ts"] = a.last_modified()
    return d


def all(uow: AbstractUnitOfWork = None, bus: MessageBus = None) -> List[Dict]:
    if not uow:
        uow = bus.uows.get(model.AssetRelease)
    with uow:
        repo: AssetReleaseRepository = uow.repo  # type: ignore
        return [to_flat_dict(r) for r in repo.all()]


def get(
    release: str, uow: AbstractUnitOfWork = None, bus: MessageBus = None
) -> Optional[Dict]:
    if not uow:
        uow = bus.uows.get(model.AssetRelease)
    with uow:
        repo: AssetReleaseRepository = uow.repo  # type: ignore
        return to_flat_dict(repo.get(DomainId(release)))


def get_releases(
    user: str,
    active=True,
    uow: AbstractUnitOfWork = None,
    bus: MessageBus = None,
) -> List[Dict]:
    if not uow:
        uow = bus.uows.get(model.AssetRelease)
    with uow:
        # TODO implement me with native access??
        repo: AssetReleaseRepository = uow.repo  # type: ignore
        if active:
            releases = repo.user_active_releases(UserId(user))
        else:
            releases = repo.user_past_releases(UserId(user))
        return [to_flat_dict(r) for r in releases]


def get_incoming_releases(
    user: str,
    uow: AbstractUnitOfWork = None,
    bus: MessageBus = None,
) -> List[Dict]:
    extra_cond = {
        "$or": [
            {"conditions.release_ts": {"$lt": now_utc_millis()}},
            {"conditions.type": {"$ne": "time_condition"}},
        ]
    }
    if not uow:
        uow = bus.uows.get(model.AssetRelease)
    with uow:
        repo: AssetReleaseMongoRepo = uow.repo  # type: ignore
        releases = [
            to_flat_dict(r)
            for r in repo.all(
                receiver=user, pending=True, extra_conditions=extra_cond
            )
        ]
    return releases


def user_stats(user_id: str, bus: MessageBus = None) -> Dict:
    return {
        "total": 2,
        "in_a_bottle": 20,
        "hide_and_seek": 2,
        "future_self": 7,
        "time_capsule": 3,
    }


def pending(user_id: str, bus=None) -> int:
    with mongo_client() as client:
        col = client.assets.legacy
        filter = {
            "receivers": user_id,
            "state": RootAggState.ACTIVE.value,
            "$or": [
                {"conditions.release_ts": {"$lt": now_utc_millis()}},
                {"conditions.type": {"$ne": "time_condition"}},
            ],
        }
        num_pending = col.count_documents(filter)

    return num_pending


def users_with_incoming_releases(since: int, to: int = now_utc_millis(),
                                 bus: MessageBus = None) -> Dict[str, int]:
    """
    Returns the users with incoming releases since a time to another time

    :param since:
    :param to: Upper limit (lt). Default: now_utc_millis()
    :param bus:
    :return: Dict[UserID, # of incoming releases in this time]
    """
    with bus.uows.get(model.AssetRelease) as uow:
        client = uow.repo._client
        db = uow.repo.db
        filter = {
            "state": RootAggState.ACTIVE.value,
            "conditions.release_ts": {
                    "$gte": since,
                    "$lt": to,
            }
        }
        logger.debug(f"Using filters {filter}", component="mongo")
        legacy_cursor = client[db].legacy.aggregate(
            [
                {"$match": filter},
                {"$unwind": {"path": "$receivers"}},
                {"$group": {"_id": "$receivers", "count": {"$sum": 1}}},
            ]
        )
        resp = {res["_id"]: res["count"] for res in legacy_cursor}

        return resp