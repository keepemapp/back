from datetime import datetime
from typing import Optional, List, Type


from emo.shared.domain import AssetId, UserId
from emo.shared.domain.usecase import Command
from emo.shared.domain.usecase.validations import user_owns_all_assets
from emo.assets.domain.entity.asset import AssetRepository
from emo.assets.domain.entity.transfer import Transfer
from emo.assets.domain.usecase.transfer import TransferCreated


class CreateTimeCapsule(Command):
    """
    Save away some assets that will be reappear in a later point in time
    to the individuals you specify.

    Input: Transaction
    Output: TransferCreated event

    Rules:
    1. The person using it must own the assets
    2. scheduled date must be in the future
    """

    def __int__(self,
                asset_repo: Type[AssetRepository],
                transferor_id: UserId,
                receiver_ids: List[UserId],
                asset_ids: List[AssetId],
                scheduled_date: datetime,
                title: Optional[str] = None,
                description: Optional[str] = None
                ):
        if scheduled_date <= datetime.utcnow():
            raise Exception("Note to future self scheduled date is in the past. This is not allowed.")
        elif not user_owns_all_assets(asset_repo, transferor_id, asset_ids):
            raise Exception("Some of the selected assets are not owned by you")

        transfer = Transfer(transferor_id=transferor_id,
                            receiver_ids=receiver_ids,
                            asset_ids=asset_ids,
                            scheduled_date=scheduled_date,
                            title=title,
                            description=description
                            )
        self.event = TransferCreated(aggregate=transfer)

    def execute(self) -> TransferCreated:
        return self.event
