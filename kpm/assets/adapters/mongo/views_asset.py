import random
from dataclasses import asdict
from typing import Dict, List, Optional

import flatdict
from pymongo import MongoClient

from kpm.assets.domain.model import Asset
from kpm.assets.service_layer.unit_of_work import AssetUoW
from kpm.shared.adapters.mongo import mongo_client
from kpm.shared.domain.model import AssetId, RootAggState, UserId
from kpm.shared.log import logger
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
    filter = {
        "_id": {"$in": assets},
        "owners": user
    }
    with mongo_client() as client:
        col = client['assets'].assets
        num_found = col.count_documents(filter=filter)
    return num_found == len(assets)


def find_by_ownerid(
    user_id: str, uow: AssetUoW = None, bus: MessageBus = None, **kwargs
) -> List[Dict]:
    if not uow:
        uow = bus.uows.get(Asset)
    with uow:
        return [
            asset_to_flat_dict(a)
            for a in uow.repo.find_by_ownerid(UserId(user_id), **kwargs)
        ]


def assets_of_the_week(user_id: str, bus: MessageBus = None) -> List[Dict]:
    filter = {'owners_id': user_id, "state": RootAggState.ACTIVE}
    fields = ['_id', 'title', 'file.type']
    limit_results = 2
    results = []
    with mongo_client() as client:
        col = client['assets'].assets
        assets = col.aggregate([
            {"$match": filter},
            {"$sample": {"size": limit_results}},
            {"$projection": fields}
        ])
        for a in assets:
            results.append({"id": a["_id"], "title": a["title"],
                            "file_type": a["file"]["type"]})
    logger.debug(f"Assets of the week selected for {user_id}: {results}")
    return results


def user_stats(user_id: str, bus: MessageBus = None) -> Dict:
    type_agg = [
        {"$match": {"owners_id": user_id}},
        {"$group": {
            "_id": "$file.type",
            "count": {"$sum": 1},
            "size:": {"$sum": "file.size_bytes"}
        }},
    ]
    with mongo_client() as client:
        col = client['assets'].assets
        res = col.aggregate(type_agg)
    print(res)
    return {
        "total": 32,
        "images": 20,
        "documents": 2,
        "videos": 7,
        "audios": 3,
        "others": 0,
        "visible": 28,
    }
