from dataclasses import asdict
from typing import Dict, List, Optional

import flatdict

import kpm.assets.domain.model as model
from kpm.assets.domain.repositories import AssetReleaseRepository
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import UserId
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
    if not uow:
        uow = bus.uows.get(model.AssetRelease)
    with uow:
        repo: AssetReleaseRepository = uow.repo  # type: ignore
        releases = [
            r
            for r in repo.all()
            if UserId(id=user) in r.receivers and r.is_active()
        ]
    incoming = []
    # Keep just where the scheduled time is in the past so they can trigger
    for r in releases:
        for c in r.conditions:
            if isinstance(c, model.TimeCondition) and c.is_met():
                incoming.append(r)
    return [to_flat_dict(r) for r in incoming]


def user_stats(user_id: str, bus: MessageBus = None) -> Dict:
    return {
        "total": 2,
        "in_a_bottle": 20,
        "hide-and-seek": 2,
        "future_self": 7,
        "time_capsule": 3,
    }


def pending(user_id: str, bus=None) -> int:
    return len(get_incoming_releases(user_id, bus=bus))
