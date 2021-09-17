from abc import abstractmethod
from typing import List, NoReturn, Optional

from emo.assets.domain.entity.asset import Asset
from emo.shared.domain import AssetId, DomainRepository, UserId


class AssetRepository(DomainRepository):
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
    def create(self, asset: Asset) -> NoReturn:
        """Create an asset in the repository"""
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, id: AssetId) -> Optional[Asset]:
        """Find asset by asset id

        :return: Asset matching id
        :rtype: Asset, None
        """
        raise NotImplementedError

    @abstractmethod
    def find_by_ids(self, ids: List[AssetId]) -> List[Asset]:
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
    def delete_by_id(self, id: AssetId) -> NoReturn:
        """Deletes asset matching the ID.

        ATTENTION: if ID does not exist, it does not raise anything.
        """
        raise NotImplementedError
