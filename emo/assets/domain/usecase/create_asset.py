import os.path as path
from dataclasses import dataclass, field
from typing import List, Optional

from emo.assets.domain.entity.asset import Asset, FileData
from emo.assets.domain.usecase.unit_of_work import AssetUoW
from emo.shared.domain import AssetId, Command, Event, UserId, init_id
from emo.shared.domain.time_utils import current_utc_timestamp


@dataclass(frozen=True)
class AssetCreated(Event):
    eventType: str = "asset_created"


@dataclass(frozen=True)
class CreateAsset(Command):
    title: str
    description: str
    owners_id: List[str]
    file_type: str
    file_name: str
    id: Optional[str] = field(default_factory=lambda: init_id(AssetId).id)


def _compute_location(owner_id: str, asset_id: str) -> str:
    return path.join(owner_id, asset_id + ".enc")


def create_asset(cmd: CreateAsset, uow: AssetUoW):
    """Handler to create an asset

    :param cmd: Command
    :type cmd: CreateAsset
    :param uow: Unit of Work instance
    :type uow: AssetUoW
    :return:
    """
    asset = Asset(
        created_at=current_utc_timestamp(),
        owners_id=[UserId(u) for u in cmd.owners_id],
        file=FileData(
            type=cmd.file_type,
            name=cmd.file_name,
            location=_compute_location(cmd.owners_id[0], cmd.id),
        ),
        id=AssetId(cmd.id),
        title=cmd.title,
        description=cmd.description,
    )
    with uow:
        uow.repo.create(asset)
        uow.commit()
