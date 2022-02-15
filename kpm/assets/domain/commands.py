from dataclasses import field
from typing import Dict, List, Optional, Set

from pydantic.dataclasses import dataclass

from kpm.shared.domain import init_id, required_field
from kpm.shared.domain.commands import Command
from kpm.shared.domain.model import AssetId
from kpm.shared.domain.time_utils import from_now_ms


@dataclass(frozen=True)
class CreateAsset(Command):
    title: str = required_field()  # type: ignore
    owners_id: List[str] = required_field()  # type: ignore
    file_type: str = required_field()  # type: ignore
    file_name: str = required_field()  # type: ignore
    file_size_bytes: int = required_field()  # type: ignore
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
class RemoveAsset(Command):
    asset_id: str = required_field()  # type: ignore


@dataclass(frozen=True)
class CreateAssetInABottle(Command):
    assets: List[str] = required_field()  # type: ignore
    """UNIX timestamp in milliseconds"""
    min_date: int = field(default_factory=lambda: from_now_ms(months=1))
    """UNIX timestamp in milliseconds"""
    max_date: int = field(default_factory=lambda: from_now_ms(years=5))
    name: str = required_field()  # type: ignore
    receivers: List[str] = required_field()  # type: ignore
    owner: str = required_field()  # type: ignore
    description: Optional[str] = None
    aggregate_id: str = field(default_factory=lambda: init_id().id)

    def __post_init__(self):
        if self.max_date < self.min_date:
            raise ValueError("Mix and Max dates are swapped")


@dataclass(frozen=True)
class CreateAssetToFutureSelf(Command):
    assets: List[str] = required_field()  # type: ignore
    owner: str = required_field()  # type: ignore
    """UNIX timestamp in milliseconds"""
    scheduled_date: int = required_field()  # type: ignore
    name: str = required_field()  # type: ignore
    description: Optional[str] = None
    aggregate_id: str = field(default_factory=lambda: init_id().id)


@dataclass(frozen=True)
class TriggerRelease(Command):
    by_user: str = required_field()  # type: ignore
    aggregate_id: str = required_field()  # type: ignore
    """Optional field for the geographical conditions."""
    geo_location: Optional[str] = None


@dataclass(frozen=True)
class CancelRelease(Command):
    aggregate_id: str = required_field()  # type: ignore


@dataclass(frozen=True)
class CreateHideAndSeek(Command):
    """ """

    assets: List[str] = required_field()  # type: ignore
    # TODO have a good location class
    location: str = required_field()  # type: ignore
    name: str = required_field()  # type: ignore
    description: Optional[str] = None
    owner: str = required_field()  # type: ignore
    receivers: List[str] = required_field()  # type: ignore
    aggregate_id: str = field(default_factory=lambda: init_id().id)


@dataclass(frozen=True)
class CreateTimeCapsule(Command):
    assets: List[str] = required_field()  # type: ignore
    name: str = required_field()  # type: ignore
    location: str = required_field()  # type: ignore
    scheduled_date: int = required_field()  # type: ignore
    description: Optional[str] = None
    owner: str = required_field()  # type: ignore
    receivers: List[str] = required_field()  # type: ignore
    aggregate_id: str = field(default_factory=lambda: init_id().id)


@dataclass(frozen=True)
class TransferAssets(Command):
    """"""

    assets: List[str] = required_field()  # type: ignore
    name: str = required_field()  # type: ignore
    owner: str = required_field()  # type: ignore
    receivers: List[str] = required_field()  # type: ignore
    description: Optional[str] = None
    aggregate_id: str = field(default_factory=lambda: init_id().id)


@dataclass(frozen=True)
class UploadAssetFile(Command):
    """Uploads an asset file"""

    asset_id: str = required_field()  # type: ignore
