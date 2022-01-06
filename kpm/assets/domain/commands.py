from dataclasses import dataclass, field
from typing import Dict, List, Optional

from kpm.shared.domain import init_id, required_field
from kpm.shared.domain.commands import Command
from kpm.shared.domain.model import AssetId


@dataclass(frozen=True)
class CreateAsset(Command):
    title: str = required_field()
    owners_id: List[str] = required_field()
    file_type: str = required_field()
    file_name: str = required_field()
    description: Optional[str] = None
    asset_id: Optional[str] = field(
        default_factory=lambda: init_id(AssetId).id
    )


@dataclass(frozen=True)
class CreateAssetInABottle(Command):
    assets: List[str] = required_field()
    """UNIX timestamp in milliseconds"""
    scheduled_date: int = required_field()
    name: str = required_field()
    receivers: List[str] = required_field()
    owner: str = required_field()
    description: str = None
    aggregate_id: str = field(default_factory=init_id().id)


@dataclass(frozen=True)
class CreateAssetToFutureSelf(Command):
    assets: List[str] = required_field()
    owner: str = required_field()
    """UNIX timestamp in milliseconds"""
    scheduled_date: int = required_field()
    name: str = required_field()
    description: str = None
    aggregate_id: str = field(default_factory=lambda: init_id().id)


@dataclass(frozen=True)
class TriggerRelease(Command):
    aggregate_id: str = required_field()


@dataclass(frozen=True)
class CancelRelease(Command):
    aggregate_id: str = required_field()


@dataclass(frozen=True)
class Stash(Command):
    """ """

    asset_ids: List[str] = required_field()
    location: Dict = required_field()  # TODO have a good location class
    name: str = required_field()
    description: str = required_field()
    owner: str = required_field()
    receivers: List[str] = required_field()
    aggregate_id: str = field(default_factory=lambda: init_id().id)


@dataclass(frozen=True)
class CreateTimeCapsule(Command):
    asset_ids: List[str] = required_field()
    name: str = required_field()
    description: str = required_field()
    owners_id: List[str] = required_field()
    aggregate_id: str = field(default_factory=lambda: init_id().id)


@dataclass(frozen=True)
class TransferAssets(Command):
    """"""

    asset_ids: List[str] = required_field()
    name: str = required_field()
    owner: str = required_field()
    receivers: List[str] = required_field()
    description: str = None
    aggregate_id: str = field(default_factory=lambda: init_id().id)


@dataclass(frozen=True)
class UploadAssetFile(Command):
    """Uploads an asset file"""

    asset_id: str = required_field()
