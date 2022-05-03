from dataclasses import asdict
from os import path as path
from typing import Union

import kpm.assets.domain.commands as cmds
import kpm.assets.domain.events as events
from kpm.assets.domain.model import Asset, BequestType, FileData
from kpm.assets.domain.repositories import AssetRepository
from kpm.assets.service_layer.unit_of_work import AssetUoW
from kpm.settings import settings as s
from kpm.shared.domain.model import AssetId, RemovalNotPossible, UserId
from kpm.shared.domain.time_utils import now_utc_millis
from kpm.shared.security.chacha20poly import ChaCha20PolyFileCypher
from kpm.users.domain.events import UserRemoved


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
    if event.bequest_type == BequestType.SELF.value:
        return
    with asset_uow as uow:
        for aid in event.assets:
            a: Asset = uow.repo.find_by_id(AssetId(aid), visible_only=False)
            if event.bequest_type == BequestType.GIFT.value:
                a.change_owner(event.timestamp, event.owner, event.receivers)
                a.update_fields(event.timestamp, {"bookmarked": False})
                uow.repo.update(a)
            elif event.bequest_type == BequestType.CO_OWNSRSHIP.value:
                new_owners = event.receivers + [event.owner]
                a.change_owner(event.timestamp, event.owner, new_owners)
                uow.repo.update(a)
            elif event.bequest_type == BequestType.COPY.value:
                raise NotImplementedError()
            else:
                raise NotImplementedError()
        uow.commit()


def _compute_location(asset_id: str) -> str:
    return path.join(asset_id[:4], asset_id + ".enc")


def create_asset(cmd: cmds.CreateAsset, asset_uow: AssetUoW):
    """Handler to create an asset

    :param cmd: Command
    :type cmd: CreateAsset
    :param asset_uow: Unit of Work instance
    :type asset_uow: AssetUoW
    :return:
    """
    dic = asdict(cmd)
    dic["owners_id"] = [UserId(u) for u in dic.pop("owners_id")]
    dic["id"] = AssetId(dic.pop("asset_id"))

    dic["file"] = FileData(
        type=dic.pop("file_type"),
        name=dic.pop("file_name"),
        location=_compute_location(cmd.asset_id),
        size_bytes=dic.pop("file_size_bytes"),
        encryption_type="ChaCha20PolyFileCypher",
        encryption_key=ChaCha20PolyFileCypher.generate_data_key(
            s.DATA_KEY_ENCRYPTION_KEY
        ),
    )
    dic["created_ts"] = dic.pop("timestamp")
    asset = Asset(**{k: v for k, v in dic.items() if v is not None})
    with asset_uow:
        asset_uow.repo.create(asset)
        asset_uow.commit()


def update_asset_fields(cmd: cmds.UpdateAssetFields, asset_uow: AssetUoW):
    with asset_uow as uow:
        a = uow.repo.find_by_id(AssetId(cmd.asset_id), visible_only=False)
        a.update_fields(mod_ts=cmd.timestamp, updates=cmd.update_dict())
        uow.repo.update(a)
        uow.commit()


def remove_asset(cmd: cmds.RemoveAsset, asset_uow: AssetUoW):
    # TODO remove file
    # TODO handle what happens if there are multiple owners involved
    with asset_uow as uow:
        a = uow.repo.find_by_id(AssetId(cmd.asset_id), visible_only=True)
        if isinstance(a, Asset):
            a.remove(mod_ts=cmd.timestamp)
            uow.repo.update(a)
            uow.commit()
        else:
            raise RemovalNotPossible(
                "Asset has releases on it. " "Please remove it from them."
            )


def asset_file_upload(cmd: cmds.UploadAssetFile, asset_uow: AssetUoW):
    with asset_uow as uow:
        a = uow.repo.find_by_id(AssetId(cmd.asset_id), visible_only=False)
        ts = now_utc_millis()
        a.upload_file(ts)
        uow.repo.update(a)
        uow.commit()


def remove_user_assets(event: UserRemoved, asset_uow: AssetUoW):
    """Removes all the releases of a removed user

    TO THINK: should we instead trigger the commands RemoveAsset?
    """
    uid = UserId(id=event.aggregate_id)
    with asset_uow as uow:
        repo: AssetRepository = uow.repo
        assets = repo.find_by_ownerid(uid=uid)
        for a in assets:
            if len(a.owners_id) == 1:
                # TODO remove file
                a.remove(mod_ts=event.timestamp)
            else:
                a.change_owner(mod_ts=event.timestamp, transferor=uid, new=[])
            uow.repo.update(a)
        uow.commit()
