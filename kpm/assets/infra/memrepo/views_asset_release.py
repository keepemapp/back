from dataclasses import asdict
from typing import Dict, List, Optional

import flatdict

import kpm.assets.domain.entity.asset_release as ar
from kpm.shared.domain import DomainId, UserId
from kpm.shared.domain.usecase.unit_of_work import AbstractUnitOfWork


def to_flat_dict(a: ar.AssetRelease):
    if not a:
        return None
    d = dict(flatdict.FlatDict(asdict(a), delimiter="_"))
    d["id"] = d.pop("id_id")
    d["owner"] = d.pop("owner_id")
    d["receivers"] = [id["id"] for id in d.pop("receivers")]
    d["assets"] = [id["id"] for id in d.pop("assets")]
    del d["_events"]
    d.pop("conditions")
    d["conditions"] = {}
    for c in a.conditions:
        if isinstance(c, ar.TrueCondition):
            d["conditions"]["immediate"] = True
        elif isinstance(c, ar.TimeCondition):
            d["conditions"]["release_time"] = c.release_ts
    d["modified_ts"] = a.last_modified()
    return d


def all(uow: AbstractUnitOfWork) -> List[Dict]:
    with uow:
        return [to_flat_dict(r) for r in uow.repo.all()]


def get(release: str, uow: AbstractUnitOfWork) -> Optional[Dict]:
    with uow:
        return to_flat_dict(uow.repo.get(DomainId(release)))


def get_releases(
    user: str, uow: AbstractUnitOfWork, active=True
) -> List[Dict]:
    with uow:
        if active:
            releases = uow.repo.user_active_releases(UserId(user))
        else:
            releases = uow.repo.user_past_releases(UserId(user))
        return [to_flat_dict(r) for r in releases]
