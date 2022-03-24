from __future__ import annotations

from abc import ABC, abstractmethod
from tempfile import TemporaryFile
from typing import List, Optional, Set

from kpm.assets.domain.model import Asset, AssetRelease
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import AssetId, UserId
from kpm.shared.domain.repository import DomainRepository


class AssetRepository(DomainRepository):
    def __init__(self, **kwargs):
        super(AssetRepository, self).__init__(**kwargs)
        self._seen: Set[Asset] = set()

    @abstractmethod
    def _query(
        self,
        *,
        ids: List[AssetId] = None,
        owners: List[UserId] = None,
        order_by: str = None,
        order: str = "asc",
        visible_only: bool = True,
        asset_types: List[str] = None,
        bookmarked: Optional[bool] = None,
    ) -> List[Asset]:
        raise NotImplementedError

    def all(self, **kwargs) -> List[Asset]:
        """Returns all the assets

        To get all the assets all the owner has access to use
        `find_by_ownerid(uid)` method
        :returns: List of all the assets
        :rtype: List[Asset]
        """
        if not kwargs.get("visible_only"):
            kwargs["visible_only"] = False
        return self._query(**kwargs)

    @abstractmethod
    def create(self, asset: Asset) -> None:
        """Create an asset in the repository"""
        raise NotImplementedError

    @abstractmethod
    def update(self, asset: Asset) -> None:
        """Updates an asset"""
        raise NotImplementedError

    def find_by_id(self, id: AssetId, **kwargs) -> Optional[Asset]:
        """Find asset by asset id

        :return: Asset matching id
        :rtype: Asset, None
        """
        ids = self.find_by_ids([id], **kwargs)
        return ids[0] if ids else None

    def find_by_ids(self, ids: List[AssetId], **kwargs) -> List[Asset]:
        """Finds assets in list that are in the database.

        If one id does not exist, it does not return it so you
        might end up with a smaller list than inputed.
        :parameter ids: list of asset ids to search for
        :type: List[AssetId]

        :returns: List of matching assets
        :rtype: List[Asset]
        """
        return self._query(ids=ids, **kwargs)

    def find_by_ownerid(self, uid: UserId, **kwargs) -> List[Asset]:
        """Finds all the assets the user is owner of.

        :parameter uid: user ID
        :type: UserId

        :returns: List of matching assets
        :rtype: List[Asset]
        """

        return self._query(owners=[uid], **kwargs)

    def find_by_id_and_ownerid(
        self, aid: AssetId, uid: UserId, **kwargs
    ) -> Optional[Asset]:
        """Finds all the assets the user is owner of.

        :parameter aid:  asset ID
        :type: AssetId
        :parameter uid: user ID
        :type: UserId

        :returns: List of matching assets
        :rtype: List[Asset]
        """
        ids = self._query(owners=[uid], ids=[aid], **kwargs)
        return ids[0] if ids else None

    @abstractmethod
    def remove(self, id: AssetId) -> None:
        """Removes asset matching the ID from the database. Use it with care.

        ATTENTION: if ID does not exist, it does not raise anything.
        """
        raise NotImplementedError


class AssetReleaseRepository(DomainRepository):
    def __init__(self):
        super().__init__()
        self._seen: Set[AssetRelease] = set()

    @abstractmethod
    def put(self, release: AssetRelease):
        raise NotImplementedError

    @abstractmethod
    def exists(self, owner: UserId, name: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get(self, release_id: DomainId) -> Optional[AssetRelease]:
        raise NotImplementedError

    @abstractmethod
    def user_active_releases(self, user_id: UserId) -> List[AssetRelease]:
        raise NotImplementedError

    @abstractmethod
    def user_past_releases(self, user_id: UserId) -> List[AssetRelease]:
        raise NotImplementedError

    @abstractmethod
    def all(self) -> List[AssetRelease]:
        raise NotImplementedError


class AssetFileRepository(ABC):
    @abstractmethod
    def create(self, location: str, file: TemporaryFile):
        raise NotImplementedError

    @abstractmethod
    def delete(self, location: str):
        raise NotImplementedError

    @abstractmethod
    def get(self, location: str) -> TemporaryFile:
        raise NotImplementedError


class EncryptedAssetFileRepository:
    def create(self, location: str, file: TemporaryFile):
        raise NotImplementedError

    @abstractmethod
    def _create(self, location: str, file: TemporaryFile):
        raise NotImplementedError

    @abstractmethod
    def delete(self, location: str):
        raise NotImplementedError

    def get(self, location: str) -> TemporaryFile:
        raise NotImplementedError

    @abstractmethod
    def _get(self, location: str) -> TemporaryFile:
        raise NotImplementedError