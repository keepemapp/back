from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Type

from emo.assets.domain.entity import AssetRepository
from emo.shared.domain import AssetId, RootAggregate, TransferId, UserId


@dataclass(frozen=True)
class Transfer(RootAggregate):
    transferor_id: UserId
    receiver_ids: List[UserId]
    asset_ids: List[AssetId]
    scheduled_date: datetime
    id: TransferId
    title: Optional[str]
    description: Optional[str]

    def is_future(self) -> bool:
        return self.scheduled_date <= datetime.utcnow()

    def execute(
        self,
        asset_repo: Type[AssetRepository],
    ):
        """TODO
        Executes the logic to transfer the assets

        . Ensure new users can access the assets (FUTURE)
        . Move the files
        . Create new asset per user
        . Notify users on transfer

        :return:
        """
        assets = asset_repo.find_by_ids(self.transferor_id, self.asset_ids)

        for a in assets:
            a.transfer()

        pass
