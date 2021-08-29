from dataclasses import dataclass
from typing import Optional

from emo.assets.domain.entity.asset import Asset
from emo.assets.domain.entity.condition_to_live import ConditionToLive
from emo.shared.domain import AssetId, UserId, init_id
from emo.shared.domain.usecase import Command, Event


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

    def __init__(
        self,
        owner_id: UserId,
        type: str,
        file_name: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        conditionToLive: Optional[ConditionToLive] = None,
    ):
        a = Asset(
            owner_id=owner_id,
            type=type,
            file_name=file_name,
            id=init_id(AssetId),
            title=title,
            description=description,
            conditionToLive=conditionToLive,
        )

        self.event = AssetCreated(aggregate=a)

    def execute(self) -> AssetCreated:
        return self.event
