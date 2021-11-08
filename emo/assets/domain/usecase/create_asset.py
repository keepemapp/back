import os.path as path
from dataclasses import dataclass, field
from typing import List, Optional

from emo.assets.domain.entity.asset import Asset, FileData
from emo.assets.domain.usecase.unit_of_work import AssetUoW
from emo.shared.domain import AssetId, Command, Event, UserId, init_id


@dataclass(frozen=True)
class AssetCreated(Event):
    eventType: str = "asset_created"


@dataclass(frozen=True)
class CreateAsset(Command):
    title: str
    owners_id: List[str]
    file_type: str
    file_name: str
    description: Optional[str] = None
    asset_id: Optional[str] = field(
        default_factory=lambda: init_id(AssetId).id
    )


def _compute_location(owner_id: str, asset_id: str) -> str:
    return path.join(owner_id, asset_id + ".enc")


def create_asset(cmd: CreateAsset, asset_uow: AssetUoW):
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
