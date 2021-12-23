from dataclasses import dataclass, field
from typing import Dict, List, Optional

from kpm.shared.domain import init_id, required_field
from kpm.shared.domain.commands import Command
from kpm.shared.domain.events import Event
from kpm.shared.domain.model import AssetId


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


@dataclass(frozen=True)
class CreateAssetInABottle(Command):
    assets: List[str]
    """UNIX timestamp in milliseconds"""
    scheduled_date: int
    name: str
    receivers: List[str]
    owner: str
    description: str = None
    aggregate_id: str = field(default_factory=init_id().id)


@dataclass(frozen=True)
class CreateAssetToFutureSelf(Command):
    assets: List[str]
    owner: str
    """UNIX timestamp in milliseconds"""
    scheduled_date: int
    name: str
    description: str = None
    aggregate_id: str = field(default_factory=lambda: init_id().id)


@dataclass(frozen=True)
class TriggerRelease(Command):
    aggregate_id: str


@dataclass(frozen=True)
class CancelRelease(Command):
    aggregate_id: str


@dataclass(frozen=True)
class Stash(Command):
    """ """

    asset_ids: List[str]
    location: Dict  # TODO have a good location class
    name: str
    description: str
    owner: str
    receivers: List[str]
    aggregate_id: str = field(default_factory=lambda: init_id().id)


@dataclass(frozen=True)
class CreateTimeCapsule(Command):
    asset_ids: List[str]
    name: str
    description: str
    owners_id: List[str]
    aggregate_id: str = field(default_factory=lambda: init_id().id)


@dataclass(frozen=True)
class TransferAssets(Command):
    """"""

    asset_ids: List[str]
    name: str
    owner: str
    receivers: List[str]
    description: str = None
    aggregate_id: str = field(default_factory=lambda: init_id().id)


@dataclass(frozen=True)
class AssetOwnershipChanged(Event):
    owners: List[str] = required_field()
    eventType: str = "AssetOwnershipChanged"
