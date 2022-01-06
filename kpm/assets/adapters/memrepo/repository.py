import os
import pickle
from pathlib import Path
from typing import Dict, List, NoReturn, Optional, Set, Union

from kpm.assets.domain.model import (Asset, AssetRelease,
                                     DuplicatedAssetException)
from kpm.assets.domain.repositories import (AssetReleaseRepository,
                                            AssetRepository)
from kpm.settings import settings
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import AssetId, UserId

Assets = Dict[AssetId, Asset]
OwnerIndex = Dict[UserId, Set[AssetId]]


class MemoryAssetRepository(AssetRepository):
    def __init__(
        self,
    ):
        super(MemoryAssetRepository, self).__init__()
        self._repo: Assets = {}
        self._owner_index: OwnerIndex = {}

    def _query(self, *, ids: List[AssetId] = None, owners: List[UserId] = None,
               order_by: str = None, order_by_order: str = "asc",
               visible_only: bool = True, asset_types: List[str] = None
               ) -> List[Asset]:

        ids = ids if ids else []
        if owners:
            oas = set()
            for uid in owners:
                oas = oas.union(set(self._owner_index.get(uid, [])))
            if ids:
                ids = set(ids).intersection(oas)
            else:
                ids = oas
            if len(ids) < 1:
                return []

        # Filtering results from the dict
        results = []
        for aid, asset in self._repo.items():
            filters = []
            # Filters
            if ids:
                filters.append(aid in ids)
            if owners:
                filters.append(any(o in owners for o in asset.owners_id))
            if visible_only:
                filters.append(asset.is_visible())
            if asset_types:
                filters.append(asset.file.type in asset_types)

            if all(filters):  # Select if all filters are true
                results.append(asset)

        # Sorting by order_by attribute
        if order_by:
            is_reverse = order_by_order == "desc"
            results.sort(reverse=is_reverse,
                         key=lambda a: getattr(a, order_by))

        return results

    def create(self, asset: Asset) -> NoReturn:
        if self._repo.get(asset.id):
            raise DuplicatedAssetException()
        self.update(asset)

    def update(self, asset: Asset) -> None:
        for oid in asset.owners_id:
            if oid in self._owner_index:
                self._owner_index[oid].add(asset.id)
            else:
                self._owner_index[oid] = {asset.id}
        self._repo[asset.id] = asset
        self._seen.add(asset)

    def _delete(self, asset: Asset):
        owners = asset.owners_id
        try:
            del self._repo[asset.id]
            for oid in owners:
                self._owner_index[oid] = set([
                    a for a in self._owner_index[oid] if a != asset.id
                ])
        except KeyError:
            pass

    def delete(self, id: AssetId) -> NoReturn:
        asset = self.find_by_id(id)
        if asset:
            self._delete(asset)

    def commit(self) -> None:
        pass


class MemoryPersistedAssetRepository(MemoryAssetRepository):
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
