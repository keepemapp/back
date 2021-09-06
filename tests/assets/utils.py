from typing import Any, Dict, List, NoReturn, Optional

from emo.assets.domain.entity import Asset, AssetRepository
from emo.shared.domain import AssetId, UserId

Assets = Dict[AssetId, Asset]
OwnerIndex = Dict[UserId, List[AssetId]]


class MemoryAssetRepository(AssetRepository):
    def __init__(self):
        self._repo: Assets = {}
        self._owner_index: OwnerIndex = {}

    def create(self, asset: Asset) -> Any:
        self._repo[asset.id] = asset
        for oid in asset.owners_id:
            if oid in self._owner_index:
                self._owner_index[oid].append(asset.id)
            else:
                self._owner_index[oid] = [asset.id]

    def find_by_id(self, id: AssetId) -> Optional[Asset]:
        ids = self.find_by_ids([id])
        return ids[0] if ids else None

    def find_by_ids(self, ids: List[AssetId]) -> List[Asset]:
        return [v for k, v in self._repo.items() if k in ids]

    def delete(self, asset: Asset):
        owners = asset.owners_id
        for oid in owners:
            self._owner_index[oid] = [
                a for a in self._owner_index[oid] if a != asset.id
            ]
        del self._repo[asset.id]

    def delete_by_id(self, id: AssetId):
        self.delete(self.find_by_id(id))

    def find_by_ownerid(self, uid: UserId) -> List[Asset]:
        asset_ids = self._owner_index.get(uid, [])
        return self.find_by_ids(asset_ids)

    def all(self) -> List[Asset]:
        return list(self._repo.values())

    def clean_all(self):
        self._repo.clear()
        self._owner_index.clear()
