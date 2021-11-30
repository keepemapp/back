from typing import Union

import kpm.assets.domain.entity.asset_release as ar
from kpm.assets.domain.entity.asset import Asset
from kpm.assets.domain.usecase.unit_of_work import AssetUoW
from kpm.shared.domain import AssetId


def hide_asset(event: ar.AssetReleaseScheduled, asset_uow: AssetUoW):
    with asset_uow as uow:
        for aid in event.assets:
            a: Asset = uow.repo.find_by_id(AssetId(aid))
            a.hide(event.timestamp)
            uow.repo.update(a)
        uow.commit()


Visible = Union[ar.AssetReleased, ar.AssetReleaseCanceled]


def make_asset_visible(event: Visible, asset_uow: AssetUoW):
    with asset_uow as uow:
        for aid in event.assets:
            a: Asset = uow.repo.find_by_id(AssetId(aid), visible_only=False)
            a.show(event.timestamp)
            uow.repo.update(a)
        uow.commit()


def change_asset_owner(event: ar.AssetReleased, asset_uow: AssetUoW):
    with asset_uow as uow:
        for aid in event.assets:
            a: Asset = uow.repo.find_by_id(AssetId(aid), visible_only=False)
            print("PRe owners", a.owners_id)
            a.change_owner(event.timestamp, event.owner, event.receivers)
            uow.repo.update(a)
            print("post owners", a.owners_id)
        uow.commit()
