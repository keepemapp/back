from dataclasses import dataclass
from typing import Dict, List

from kpm.shared.domain import required_field
from kpm.shared.domain.events import Event


@dataclass(frozen=True)
class AssetCreated(Event):
    eventType: str = "asset_created"


@dataclass(frozen=True)
class AssetReleaseScheduled(Event):
    eventType: str = "AssetReleaseScheduled"
    re_conditions: Dict = required_field()
    re_type: str = required_field()
    owner: str = required_field()
    assets: List[str] = required_field()
    receivers: List[str] = required_field()


@dataclass(frozen=True)
class AssetReleaseCanceled(Event):
    eventType: str = "AssetReleaseCanceled"
    assets: List[str] = required_field()


@dataclass(frozen=True)
class AssetReleased(Event):
    eventType: str = "AssetReleased"
    re_type: str = required_field()
    owner: str = required_field()
    assets: List[str] = required_field()
    receivers: List[str] = required_field()
