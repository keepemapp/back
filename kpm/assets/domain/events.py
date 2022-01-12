from typing import Dict, List

from pydantic.dataclasses import dataclass

from kpm.shared.domain import required_field
from kpm.shared.domain.events import Event


@dataclass(frozen=True)
class AssetCreated(Event):
    eventType: str = "asset_created"


@dataclass(frozen=True)
class AssetReleaseScheduled(Event):
    eventType: str = "AssetReleaseScheduled"
    re_conditions: Dict = required_field()  # type: ignore
    re_type: str = required_field()  # type: ignore
    owner: str = required_field()  # type: ignore
    assets: List[str] = required_field()  # type: ignore
    receivers: List[str] = required_field()  # type: ignore


@dataclass(frozen=True)
class AssetReleaseCanceled(Event):
    eventType: str = "AssetReleaseCanceled"
    assets: List[str] = required_field()  # type: ignore


@dataclass(frozen=True)
class AssetReleased(Event):
    eventType: str = "AssetReleased"
    re_type: str = required_field()  # type: ignore
    owner: str = required_field()  # type: ignore
    assets: List[str] = required_field()  # type: ignore
    receivers: List[str] = required_field()  # type: ignore


@dataclass(frozen=True)
class AssetOwnershipChanged(Event):
    owners: List[str] = required_field()  # type: ignore
    eventType: str = "AssetOwnershipChanged"
