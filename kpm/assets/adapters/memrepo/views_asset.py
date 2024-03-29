import random
from collections import Counter
from dataclasses import asdict
from itertools import groupby
from typing import Dict, List, Optional

import flatdict

from kpm.assets.domain.model import Asset
from kpm.assets.service_layer.unit_of_work import AssetUoW
from kpm.shared.domain.model import AssetId, BETA_USER, RootAggState, UserId
from kpm.shared.service_layer.message_bus import MessageBus


def asset_to_flat_dict(a: Asset):
    d = dict(flatdict.FlatDict(asdict(a), delimiter="_"))
    d["id"] = d.pop("id_id")
    d["state"] = d.pop("state").value
    d["owners_id"] = [oid["id"] for oid in d.pop("owners_id")]
    d["modified_ts"] = a.last_modified()
    del d["events"]
    return d


def all_assets(
    uow: AssetUoW = None, bus: MessageBus = None, **kwargs
) -> List[Dict]:
    if not uow:
        uow = bus.uows.get(Asset)
    with uow:
        return [asset_to_flat_dict(a) for a in uow.repo.all(**kwargs)]


def find_by_id(
    asset_id: str, uow: AssetUoW = None, bus: MessageBus = None
) -> Optional[Dict]:
    if not uow:
        uow = bus.uows.get(Asset)
    with uow:
        asset = uow.repo.find_by_id(AssetId(asset_id))
        return asset_to_flat_dict(asset) if asset else None


def find_by_id_and_owner(
    asset_id: str, user_id: str, uow: AssetUoW = None, bus: MessageBus = None
) -> Optional[Dict]:
    if not uow:
        uow = bus.uows.get(Asset)
    with uow:
        asset = uow.repo.find_by_id_and_ownerid(
            AssetId(asset_id), UserId(user_id)
        )
        return asset_to_flat_dict(asset) if asset else None


def owned_by(asset_id: str, user_id: str, bus: MessageBus = None) -> bool:
    with bus.uows.get(Asset) as uow:
        asset = uow.repo.find_by_id_and_ownerid(
            AssetId(asset_id), UserId(user_id)
        )
        if asset:
            return True
    return False


def are_assets_active(
    assets: List[str],
    uow: AssetUoW = None,
    bus: MessageBus = None,
    user: str = None,
) -> bool:
    """Returns `True` if all assets exist and are visible.

    If a user is passed, it checks the ownership of all assets.
    """
    if not uow:
        uow = bus.uows.get(Asset)
    with uow:
        all_assets = uow.repo.find_by_ids([AssetId(a) for a in assets])
        if len(all_assets) != len(assets):
            return False
        elif user and not all(UserId(user) in a.owners_id for a in all_assets):
            return False
        else:
            return True


def find_by_ownerid(
    user_id: str, uow: AssetUoW = None, bus: MessageBus = None, **kwargs
) -> List[Dict]:
    if not uow:
        uow = bus.uows.get(Asset)
    with uow:
        return [
            asset_to_flat_dict(a)
            for a in uow.repo.find_by_ownerid(UserId(user_id), **kwargs)
            if a.state == RootAggState.ACTIVE
        ]


def assets_of_the_week(user_id: str, bus: MessageBus = None) -> List[Dict]:
    with bus.uows.get(Asset) as uow:
        assets = uow.repo.find_by_ownerid(UserId(user_id))
        if len(assets) <= 2:
            return [assets]
        choosen: List[Asset] = random.sample(assets, 2)
        return [
            {"id": a.id.id, "title": a.title, "file_type": a.file.type}
            for a in choosen
        ]


def user_stats(user_id: str, bus: MessageBus = None) -> Dict:
    def aggregate_by_file_type(lst):
        file_type = lambda a: a[0]
        lst_sorted = sorted(lst, key=file_type)
        return {
            f_type: sum([kv[1] for kv in pairs])
            for f_type, pairs in groupby(lst_sorted, file_type)
        }

    with bus.uows.get(Asset) as uow:
        assets = uow.repo.find_by_ownerid(UserId(user_id))

    asset_sizes = [
        (a.file.type.split("/")[0], a.file.size_bytes / 1024 / 1024)
        for a in assets
        if a.state == RootAggState.ACTIVE
    ]
    asset_counts = [
        (a.file.type.split("/")[0], 1)
        for a in assets
        if a.state == RootAggState.ACTIVE
    ]

    sizes_mb = aggregate_by_file_type(asset_sizes)
    count = aggregate_by_file_type(asset_counts)
    sizes_mb["total"] = sum(sizes_mb.values())
    count["total"] = sum(count.values())
    return {
        "max_size_mb": BETA_USER.storage_mb,
        "size_mb": sizes_mb,
        "count": count,
    }


def tag_cloud(user_id: str, bus: MessageBus) -> Dict:
    tags = []
    with bus.uows.get(Asset) as uow:
        assets = uow.repo.find_by_ownerid(UserId(user_id))
        for a in assets:
            tags.extend(a.tags)
    return {tag: count for tag, count in Counter(tags).most_common(8)}
