import os
import pickle
from pathlib import Path
from typing import Dict, List, NoReturn, Optional, Union

from emo.assets.domain.entity import Asset, AssetRepository
from emo.shared.domain import AssetId, UserId

Assets = Dict[AssetId, Asset]
OwnerIndex = Dict[UserId, List[AssetId]]


class DuplicatedAssetException(Exception):
    def __init__(self):
        super().__init__(
            "You have tried creating the same asset "
            "twice. This is not allowed. "
            "Try updating it."
        )


class MemoryPersistedAssetRepository(AssetRepository):
    def __init__(self, dbfile: Union[Path, str] = Path("data/assetssrepo.pk")):
        if isinstance(dbfile, str):
            dbfile = Path(dbfile)
        self.DB_FILE: Path = dbfile
        self.INDEX_FILE = Path(str(dbfile).replace(".pk", "") + "-index.pk")
        self._repo: Assets = self.__startup_db()
        self._owner_index: OwnerIndex = self.__startup_index()

    def create(self, asset: Asset) -> NoReturn:
        if self._repo.get(asset.id):
            raise
        self._repo[asset.id] = asset
        for oid in asset.owners_id:
            if oid in self._owner_index:
                self._owner_index[oid].append(asset.id)
            else:
                self._owner_index[oid] = [asset.id]
        self.__persist()

    def find_by_id(self, id: AssetId) -> Optional[Asset]:
        ids = self.find_by_ids([id])
        return ids[0] if ids else None

    def find_by_ids(self, ids: List[AssetId]) -> List[Asset]:
        return [v for k, v in self._repo.items() if k in ids]

    def delete(self, asset: Asset):
        owners = asset.owners_id
        try:
            del self._repo[asset.id]
            for oid in owners:
                self._owner_index[oid] = [
                    a for a in self._owner_index[oid] if a != asset.id
                ]
            self.__persist()
        except KeyError:
            pass

    def delete_by_id(self, id: AssetId) -> NoReturn:
        asset = self.find_by_id(id)
        if asset:
            self.delete(asset)

    def find_by_ownerid(self, uid: UserId) -> List[Asset]:
        asset_ids = self._owner_index.get(uid, [])
        return self.find_by_ids(asset_ids)

    def all(self) -> List[Asset]:
        return list(self._repo.values())

    def __persist(self) -> NoReturn:
        with open(self.DB_FILE, "wb") as f:
            pickle.dump(self._repo, f)
        with open(self.INDEX_FILE, "wb") as f:
            pickle.dump(self._owner_index, f)

    def __startup_db(self) -> Assets:
        if os.path.exists(self.DB_FILE):
            with open(self.DB_FILE, "rb") as f:
                r = pickle.load(f)
            return r
        return {}

    def __startup_index(self) -> OwnerIndex:
        if os.path.exists(self.INDEX_FILE):
            with open(self.INDEX_FILE, "rb") as f:
                r = pickle.load(f)
            return r
        return {}
