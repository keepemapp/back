from typing import Union
import emo.assets.domain.entity.asset_release as ar

from emo.assets.domain.entity.asset import Asset
from emo.assets.domain.usecase.unit_of_work import AssetUoW
from emo.shared.domain import AssetId


def hide_asset(event: ar.AssetReleaseScheduled, asset_uow: AssetUoW):
    with asset_uow as uow:
        for aid in event.assets:
            a: Asset = uow.repo.find_by_id(AssetId(aid))
            a.hide(event.timestamp)
        uow.commit()


Visible = Union[ar.AssetReleased, ar.AssetReleaseCanceled]


def make_asset_visible(event: Visible, asset_uow: AssetUoW):
    with asset_uow as uow:
        for aid in event.assets:
            a: Asset = uow.repo.find_by_id(AssetId(aid), visible_only=False)
            a.show(event.timestamp)
        uow.commit()


def change_asset_owner(event: ar.AssetReleased, asset_uow: AssetUoW):
    with asset_uow as uow:
        for aid in event.assets:
            a: Asset = uow.repo.find_by_id(AssetId(aid), visible_only=False)
            a.change_owner(event.timestamp, event.owner, event.receivers)
        uow.commit()
