from dataclasses import asdict
from typing import Dict, List, Optional

import flatdict

from kpm.assets.domain.entity.asset import Asset
from kpm.assets.domain.usecase.unit_of_work import AssetUoW
from kpm.shared.domain import AssetId, UserId


def asset_to_flat_dict(a: Asset):
    d = dict(flatdict.FlatDict(asdict(a), delimiter="_"))
    d["id"] = d.pop("id_id")
    d["owners_id"] = [oid["id"] for oid in d.pop("owners_id")]
    del d["_events"]
    return d


def all_assets(uow: AssetUoW) -> List[Dict]:
    with uow:
        return [asset_to_flat_dict(a) for a in uow.repo.all()]


def find_by_id(asset_id: str, uow: AssetUoW) -> Optional[Dict]:
    with uow:
        asset = uow.repo.find_by_id(AssetId(asset_id))
        return asset_to_flat_dict(asset) if asset else None


def find_by_id_and_owner(
    asset_id: str, user_id: str, uow: AssetUoW
) -> Optional[Dict]:
    with uow:
        asset = uow.repo.find_by_id_and_ownerid(
            AssetId(asset_id), UserId(user_id)
        )
        return asset_to_flat_dict(asset) if asset else None


def are_assets_active(uow: AssetUoW, assets: List[str], user: str = None
                      ) -> bool:
    """Returns `True` if all assets exist and are visible.

    If a user is passed, it checks the ownership of all assets.
    """
    with uow:
        all_assets = uow.repo.find_by_ids([AssetId(a) for a in assets])
        if len(all_assets) != len(assets):
            return False
        elif user and not all(UserId(user) in a.owners_id for a in all_assets):
            return False
        else:
            return True


def find_by_ownerid(user_id: str, uow: AssetUoW) -> List[Dict]:
    with uow:
        return [
            asset_to_flat_dict(a)
            for a in uow.repo.find_by_ownerid(UserId(user_id))
        ]
