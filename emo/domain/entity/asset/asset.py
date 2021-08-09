from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

from emo.shared.domain import Entity, UserId, AssetId, init_id
from emo.domain.entity.transfer import Transfer
from emo.domain.usecase.transfer import TransferCreated
from emo.domain.entity.asset.condition_to_live import ConditionToLive


@dataclass(frozen=True)
class Asset(Entity):
    owner_id: UserId
    type: str
    file_name: str
    file_location: str

    id: AssetId = init_id(AssetId)
    title: Optional[str] = None
    description: Optional[str] = None
    conditionToLive: Optional[ConditionToLive] = None

    def copy_to_user(self) -> AssetCopied:
        pass

    def delete(self) -> AssetDeleted:
        pass

    def hasexpired(self) -> bool:
        return False if not self.conditionToLive else self.conditionToLive.condition_not_met()