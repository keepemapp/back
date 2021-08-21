from dataclasses import dataclass
from typing import Optional

from emo.shared.domain import RootAggregate, UserId, AssetId, init_id
from emo.assets.domain.entity.condition_to_live import ConditionToLive


@dataclass(frozen=True)
class Asset(RootAggregate):
    owner_id: UserId
    type: str
    file_name: str
    file_location: str

    id: AssetId = init_id(AssetId)
    title: Optional[str] = None
    description: Optional[str] = None
    conditionToLive: Optional[ConditionToLive] = None

    def has_expired(self) -> bool:
        return False if not self.conditionToLive else self.conditionToLive.condition_not_met()