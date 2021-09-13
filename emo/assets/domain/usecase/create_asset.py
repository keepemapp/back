import os.path as path
from dataclasses import dataclass
from typing import List, NoReturn, Optional

from emo.assets.domain.entity.asset import Asset
from emo.assets.domain.entity.asset_repository import AssetRepository
from emo.assets.domain.entity.condition_to_live import ConditionToLive
from emo.shared.domain import AssetId, UserId, init_id
from emo.shared.domain.time_utils import current_utc_timestamp
from emo.shared.domain.usecase import Command, Event, EventPublisher


@dataclass(frozen=True)
class AssetCreated(Event):
    eventType: str = "asset_created"


class CreateAsset(Command):
    """
    Creates an asset

    Input:
    Output:

    Rules:
    1. File must already exist
    """

    _repository: AssetRepository

    def __init__(
        self,
        *,
        owners_id: List[UserId],
        type: str,
        file_name: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        conditionToLive: Optional[ConditionToLive] = None,
        repository: AssetRepository,
        message_bus: EventPublisher,
    ):
        super().__init__(repository=repository, message_bus=message_bus)
        id = init_id(AssetId)
        self.entity = Asset(
            created_at=current_utc_timestamp(),
            owners_id=owners_id,
            type=type,
            file_name=file_name,
            file_location=self._compute_location(owners_id[0], id),
            id=id,
            title=title,
            description=description,
            conditionToLive=conditionToLive,
        )
        self.event = AssetCreated(aggregate=self.entity)

    def execute(self) -> NoReturn:
        self._repository.create(self.entity)
        self._message_bus.publish(self.event)

    @staticmethod
    def _compute_location(owner_id: UserId, asset_id: AssetId) -> str:
        return path.join(owner_id.id, asset_id.id + ".enc")
