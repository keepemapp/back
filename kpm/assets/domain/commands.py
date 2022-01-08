from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from kpm.shared.domain import init_id, required_field
from kpm.shared.domain.commands import Command
from kpm.shared.domain.model import AssetId


@dataclass(frozen=True)
class CreateAsset(Command):
    title: str = required_field()  # type: ignore
    owners_id: List[str] = required_field()  # type: ignore
    file_type: str = required_field()  # type: ignore
    file_name: str = required_field()  # type: ignore
    description: Optional[str] = None
    tags: Optional[Set[str]] = None
    people: Optional[Set[str]] = None
    location: Optional[str] = None
    created_date: Optional[str] = None
    asset_id: Optional[str] = field(
        default_factory=lambda: init_id(AssetId).id
    )
    extra_private: Optional[bool] = None
    bookmarked: Optional[bool] = None


@dataclass(frozen=True)
class UpdateAssetFields(Command):
    """User updatable fields of Asset
    TODO how to dynamically generate the fields of this class
    form Asset._get_updatable_fields() ?
    """

    asset_id: str = required_field()  # type: ignore
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[Set[str]] = None
    people: Optional[Set[str]] = None
    location: Optional[str] = None
    created_date: Optional[str] = None
    extra_private: Optional[bool] = None
    bookmarked: Optional[bool] = None

    def update_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "people": self.people,
            "location": self.location,
            "created_date": self.created_date,
            "extra_private": self.extra_private,
            "bookmarked": self.bookmarked,
        }


@dataclass(frozen=True)
class CreateAssetInABottle(Command):
    assets: List[str] = required_field()  # type: ignore
    """UNIX timestamp in milliseconds"""
    scheduled_date: int = required_field()  # type: ignore
    name: str = required_field()  # type: ignore
    receivers: List[str] = required_field()  # type: ignore
    owner: str = required_field()  # type: ignore
    description: str = None
    aggregate_id: str = field(default_factory=init_id().id)


@dataclass(frozen=True)
class CreateAssetToFutureSelf(Command):
    assets: List[str] = required_field()  # type: ignore
    owner: str = required_field()  # type: ignore
    """UNIX timestamp in milliseconds"""
    scheduled_date: int = required_field()  # type: ignore
    name: str = required_field()  # type: ignore
    description: str = None
    aggregate_id: str = field(default_factory=lambda: init_id().id)


@dataclass(frozen=True)
class TriggerRelease(Command):
    aggregate_id: str = required_field()  # type: ignore


@dataclass(frozen=True)
class CancelRelease(Command):
    aggregate_id: str = required_field()  # type: ignore


@dataclass(frozen=True)
class Stash(Command):
    """ """

    asset_ids: List[str] = required_field()  # type: ignore
    # TODO have a good location class
    location: Dict = required_field()  # type: ignore
    name: str = required_field()  # type: ignore
    description: str = required_field()  # type: ignore
    owner: str = required_field()  # type: ignore
    receivers: List[str] = required_field()  # type: ignore
    aggregate_id: str = field(default_factory=lambda: init_id().id)


@dataclass(frozen=True)
class CreateTimeCapsule(Command):
    asset_ids: List[str] = required_field()  # type: ignore
    name: str = required_field()  # type: ignore
    description: str = required_field()  # type: ignore
    owners_id: List[str] = required_field()  # type: ignore
    aggregate_id: str = field(default_factory=lambda: init_id().id)


@dataclass(frozen=True)
class TransferAssets(Command):
    """"""

    asset_ids: List[str] = required_field()  # type: ignore
    name: str = required_field()  # type: ignore
    owner: str = required_field()  # type: ignore
    receivers: List[str] = required_field()  # type: ignore
    description: Optional[str] = None
    aggregate_id: str = field(default_factory=lambda: init_id().id)


@dataclass(frozen=True)
class UploadAssetFile(Command):
    """Uploads an asset file"""

    asset_id: str = required_field()  # type: ignore
