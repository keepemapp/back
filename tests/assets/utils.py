from typing import Any, Dict, List, Optional, Type

import pytest

from kpm.assets.domain.model import (
    Asset,
    AssetRelease,
    DuplicatedAssetException,
)
from kpm.assets.domain.repositories import (
    AssetReleaseRepository,
    AssetRepository,
)
from kpm.assets.entrypoints import bootstrap
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import AssetId, UserId
from kpm.shared.domain.repository import DomainRepository
from kpm.shared.service_layer.unit_of_work import AbstractUnitOfWork

Assets = Dict[AssetId, Asset]
OwnerIndex = Dict[UserId, List[AssetId]]


class MemoryAssetRepository(AssetRepository):
    def __init__(self):
        super(MemoryAssetRepository, self).__init__()
        self._repo: Assets = {}
        self._owner_index: OwnerIndex = {}

    def create(self, asset: Asset) -> Any:
        if self._repo.get(asset.id):
            raise DuplicatedAssetException()
        self._repo[asset.id] = asset
        for oid in asset.owners_id:
            if oid in self._owner_index:
                self._owner_index[oid].append(asset.id)
            else:
                self._owner_index[oid] = [asset.id]

    def update(self, asset: Asset) -> None:
        self._repo[asset.id] = asset

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

    def find_by_id_and_ownerid(
        self, aid: AssetId, uid: UserId
    ) -> Optional[Asset]:
        owner_assets = self._owner_index.get(uid, [])
        return self.find_by_id(aid) if aid in owner_assets else None

    def all(self) -> List[Asset]:
        return list(self._repo.values())

    def clean_all(self):
        self._repo.clear()
        self._owner_index.clear()


Releases = Dict[DomainId, AssetRelease]
OwnerReleaseIndex = Dict[UserId, List[DomainId]]


class MemoryReleaseRepo(AssetReleaseRepository):
    def __init__(
        self,
    ):
        super().__init__()
        self._repo: Releases = {}

    def put(self, release: AssetRelease):
        self._repo[release.id] = release
        self._seen.add(release)

    def get(self, release_id: DomainId) -> AssetRelease:
        return self._repo.get(release_id)

    def all(self) -> List[AssetRelease]:
        return list(self._repo.values())

    def user_active_releases(self, user_id: UserId) -> List[AssetRelease]:
        result = []
        for _, r in self._repo.items():
            if r.is_active() and r.owner == user_id:
                result.append(r)
        return result

    def user_past_releases(self, user_id: UserId) -> List[AssetRelease]:
        result = []
        for _, r in self._repo.items():
            if r.is_past() and r.owner == user_id:
                result.append(r)
        return result


class MemoryUoW(AbstractUnitOfWork):
    def __init__(self, repo_cls: Type[DomainRepository], **kwargs) -> None:
        super().__init__()
        self.committed = False
        self.repo = repo_cls(**kwargs)

    def __enter__(self):
        self.committed = False
        return super().__enter__()

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass


uows = {
    "asset_uow": MemoryUoW(MemoryAssetRepository),
    "release_uow": MemoryUoW(MemoryReleaseRepo),
}


@pytest.fixture
def bus():
    """Init test bus for passing it to tests"""
    return bootstrap.bootstrap(
        asset_uow=MemoryUoW(MemoryAssetRepository),
        release_uow=MemoryUoW(MemoryReleaseRepo),
    )
