from os import path as path
from typing import Union

import kpm.assets.domain.commands as cmds
import kpm.assets.domain.events as events
from kpm.assets.domain.model import Asset, FileData
from kpm.assets.service_layer.unit_of_work import AssetUoW
from kpm.shared.domain.model import AssetId, UserId
from kpm.shared.domain.time_utils import now_utc_millis


def hide_asset(event: events.AssetReleaseScheduled, asset_uow: AssetUoW):
    with asset_uow as uow:
        for aid in event.assets:
            a: Asset = uow.repo.find_by_id(AssetId(aid))
            a.hide(event.timestamp)
            uow.repo.update(a)
        uow.commit()


Visible = Union[events.AssetReleased, events.AssetReleaseCanceled]


def make_asset_visible(event: Visible, asset_uow: AssetUoW):
    with asset_uow as uow:
        for aid in event.assets:
            a: Asset = uow.repo.find_by_id(AssetId(aid), visible_only=False)
            a.show(event.timestamp)
            uow.repo.update(a)
        uow.commit()


def change_asset_owner(event: events.AssetReleased, asset_uow: AssetUoW):
    with asset_uow as uow:
        for aid in event.assets:
            a: Asset = uow.repo.find_by_id(AssetId(aid), visible_only=False)
            a.change_owner(event.timestamp, event.owner, event.receivers)
            uow.repo.update(a)
        uow.commit()


def _compute_location(owner_id: str, asset_id: str) -> str:
    return path.join(owner_id, asset_id + ".enc")


def create_asset(cmd: cmds.CreateAsset, asset_uow: AssetUoW):
    """Handler to create an asset

    :param cmd: Command
    :type cmd: CreateAsset
    :param asset_uow: Unit of Work instance
    :type asset_uow: AssetUoW
    :return:
    """
    asset = Asset(
        owners_id=[UserId(u) for u in cmd.owners_id],
        file=FileData(
            type=cmd.file_type,
            name=cmd.file_name,
            location=_compute_location(cmd.owners_id[0], cmd.asset_id),
        ),
        id=AssetId(cmd.asset_id),
        title=cmd.title,
        description=cmd.description,
    )
    with asset_uow:
        asset_uow.repo.create(asset)
        asset_uow.commit()


def asset_file_upload(cmd: cmds.UploadAssetFile, asset_uow: AssetUoW):
    with asset_uow as uow:
        a = uow.repo.find_by_id(AssetId(cmd.asset_id), visible_only=False)
        ts = now_utc_millis()
        a.upload_file(ts)
        uow.repo.update(a)
        uow.commit()
