from typing import List, Type

from emo.assets.domain.entity import AssetRepository, TransferRepository
from emo.shared.domain import AssetId, TransferId, UserId


def user_owns_all_assets(
    repo: Type[AssetRepository], owner_id: UserId, asset_ids: List[AssetId]
) -> bool:
    assets = repo.find_by_ids(owner_id, asset_ids)
    return len(assets) == len(asset_ids)


def user_owns_all_transfers(
        repo: Type[TransferRepository],
        owner_id: UserId,
        transfer_ids: List[TransferId]
) -> bool:
    assets = repo.find_by_ids(owner_id, transfer_ids)
    return len(assets) == len(transfer_ids)
