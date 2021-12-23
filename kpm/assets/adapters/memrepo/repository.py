import os
import pickle
from pathlib import Path
from typing import Dict, List, NoReturn, Optional, Union

from kpm.assets.domain.model import (Asset, AssetRelease,
                                     DuplicatedAssetException)
from kpm.assets.domain.repositories import (AssetReleaseRepository,
                                            AssetRepository)
from kpm.settings import settings
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import AssetId, UserId

Assets = Dict[AssetId, Asset]
OwnerIndex = Dict[UserId, List[AssetId]]


class MemoryPersistedAssetRepository(AssetRepository):
    def __init__(
        self,
        dbfile: Union[Path, str] = Path(
            os.path.join(settings.DATA_FOLDER, "assetssrepo.pk")
        ),
    ):
        super(MemoryPersistedAssetRepository, self).__init__()
        if isinstance(dbfile, str):
            dbfile = Path(dbfile)
        self.DB_FILE: Path = dbfile
        self.INDEX_FILE = Path(str(dbfile).replace(".pk", "") + "-index.pk")
        self._repo: Assets = self.__startup_db()
        self._owner_index: OwnerIndex = self.__startup_index()

    def create(self, asset: Asset) -> NoReturn:
        if self._repo.get(asset.id):
            raise DuplicatedAssetException()
        self._repo[asset.id] = asset
        for oid in asset.owners_id:
            if oid in self._owner_index:
                self._owner_index[oid].append(asset.id)
            else:
                self._owner_index[oid] = [asset.id]
        self._seen.add(asset)

    def update(self, asset: Asset) -> None:
        self._repo[asset.id] = asset
        self._seen.add(asset)

    def find_by_id(self, id: AssetId, visible_only=True) -> Optional[Asset]:
        ids = self.find_by_ids([id], visible_only)
        return ids[0] if ids else None

    def find_by_ids(
        self, ids: List[AssetId], visible_only=True
    ) -> List[Asset]:
        return [
            v
            for k, v in self._repo.items()
            if k in ids and (not visible_only or v.is_visible())
        ]

    def delete(self, asset: Asset):
        owners = asset.owners_id
        try:
            del self._repo[asset.id]
            for oid in owners:
                self._owner_index[oid] = [
                    a for a in self._owner_index[oid] if a != asset.id
                ]
        except KeyError:
            pass

    def delete_by_id(self, id: AssetId) -> NoReturn:
        asset = self.find_by_id(id)
        if asset:
            self.delete(asset)

    def find_by_ownerid(self, uid: UserId) -> List[Asset]:
        asset_ids = self._owner_index.get(uid, [])
        return self.find_by_ids(asset_ids)

    def find_by_id_and_ownerid(
        self, aid: AssetId, uid: UserId
    ) -> Optional[Asset]:
        owner_assets = self._owner_index.get(uid, [])
        return self.find_by_id(aid) if aid in owner_assets else None

    def all(self) -> List[Asset]:
        return list(self._repo.values())

    def commit(self) -> None:
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


Releases = Dict[DomainId, AssetRelease]
OwnerReleaseIndex = Dict[UserId, List[DomainId]]


class MemPersistedReleaseRepo(AssetReleaseRepository):
    def __init__(
        self,
        dbfile: Union[Path, str] = Path(
            os.path.join(settings.DATA_FOLDER, "assetsreleasesrepo.pk")
        ),
    ):
        super().__init__()
        if isinstance(dbfile, str):
            dbfile = Path(dbfile)
        self.DB_FILE: Path = dbfile
        self.INDEX_FILE = Path(str(dbfile).replace(".pk", "") + "-index.pk")
        self._repo: Releases = self.__startup_db()
        self._owner_index: OwnerReleaseIndex = self.__startup_index()

    def put(self, release: AssetRelease):
        self._repo[release.id] = release
        if not self._owner_index.get(release.owner):
            self._owner_index.update({release.owner: []})
        self._owner_index[release.owner].append(release.id)
        self._seen.add(release)
        self.commit()

    def get(self, release_id: DomainId) -> AssetRelease:
        return self._repo.get(release_id)

    def all(self) -> List[AssetRelease]:
        return list(self._repo.values())

    def user_active_releases(self, user_id: UserId) -> List[AssetRelease]:
        result = []
        for rid in self._owner_index.get(user_id):
            r = self.get(rid)
            if r.is_active():
                result.append(r)
        return result

    def user_past_releases(self, user_id: UserId) -> List[AssetRelease]:
        result = []
        for rid in self._owner_index.get(user_id):
            r = self.get(rid)
            if r.is_past():
                result.append(r)
        return result

    def commit(self) -> None:
        with open(self.DB_FILE, "wb") as f:
            pickle.dump(self._repo, f)
        with open(self.INDEX_FILE, "wb") as f:
            pickle.dump(self._owner_index, f)

    def __startup_db(self) -> Releases:
        if os.path.exists(self.DB_FILE):
            with open(self.DB_FILE, "rb") as f:
                r = pickle.load(f)
            return r
        return {}

    def __startup_index(self) -> OwnerReleaseIndex:
        if os.path.exists(self.INDEX_FILE):
            with open(self.INDEX_FILE, "rb") as f:
                r = pickle.load(f)
            return r
        return {}
