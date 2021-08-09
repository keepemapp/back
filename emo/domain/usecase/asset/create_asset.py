from datetime import datetime
from typing import Optional, List, Type


from emo.shared.domain import AssetId, UserId
from emo.shared.domain.usecase import Command
from emo.shared.domain import Entity, UserId, AssetId, init_id
from emo.domain.entity.asset.condition_to_live import ConditionToLive
from emo.shared.domain.usecase.validations import user_owns_all_assets
from emo.domain.entity.asset import Asset
from emo.domain.usecase.asset.events import AssetCreated
from emo.domain.usecase.transfer import TransferCreated


class CreateAsset(Command):
    """
    Creates an asset

    Input:
    Output:

    Rules:
    1. File must already exist
    """

    def __init__(self,
                 owner_id: UserId,
                 type: str,
                 file_name: str,
                 id: AssetId = init_id(AssetId),
                 title: Optional[str] = None,
                 description: Optional[str] = None,
                 conditionToLive: Optional[ConditionToLive] = None
                 ):
        a = Asset(
            owner_id=owner_id,
            type=type,
            file_name=file_name,
            id=id,
            title=title,
            description=description,
            conditionToLive=conditionToLive
        )

        self.event = AssetCreated(aggregate=a)

    def execute(self) -> AssetCreated:
        return self.event
