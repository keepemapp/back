from __future__ import annotations

from abc import abstractmethod
from typing import List, Optional, Set

from kpm.assets.domain.model import Asset, AssetRelease
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import AssetId, UserId
from kpm.shared.domain.repository import DomainRepository


class AssetRepository(DomainRepository):
    def __init__(self):
        super(AssetRepository, self).__init__()
        self._seen: Set[Asset] = set()

    @abstractmethod
    def all(self) -> List[Asset]:
        """Returns all the assets

        To get all the assets all the owner has access to use
        `find_by_ownerid(uid)` method
        :returns: List of all the assets
        :rtype: List[Asset]
        """
        raise NotImplementedError

    @abstractmethod
    def create(self, asset: Asset) -> None:
        """Create an asset in the repository"""
        raise NotImplementedError

    @abstractmethod
    def update(self, asset: Asset) -> None:
        """Updates an asset"""
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, id: AssetId, visible_only=True) -> Optional[Asset]:
        """Find asset by asset id

        :return: Asset matching id
        :rtype: Asset, None
        """
        raise NotImplementedError

    @abstractmethod
    def find_by_ids(
        self, ids: List[AssetId], visible_only=True
    ) -> List[Asset]:
        """Finds assets in list that are in the database.

        If one id does not exist, it does not return it so you
        might end up with a smaller list than inputed.
        :parameter ids: list of asset ids to search for
        :type: List[AssetId]

        :returns: List of matching assets
        :rtype: List[Asset]
        """
        raise NotImplementedError

    @abstractmethod
    def find_by_ownerid(self, uid: UserId) -> List[Asset]:
        """Finds all the assets the user is owner of.

        :parameter uid: user ID
        :type: UserId

        :returns: List of matching assets
        :rtype: List[Asset]
        """
        raise NotImplementedError

    @abstractmethod
    def find_by_id_and_ownerid(
        self, aid: AssetId, uid: UserId
    ) -> Optional[Asset]:
        """Finds all the assets the user is owner of.

        :parameter aid:  asset ID
        :type: AssetId
        :parameter uid: user ID
        :type: UserId

        :returns: List of matching assets
        :rtype: List[Asset]
        """
        raise NotImplementedError

    @abstractmethod
    def delete_by_id(self, id: AssetId) -> None:
        """Deletes asset matching the ID.

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
    def get(self, release_id: DomainId) -> AssetRelease:
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
