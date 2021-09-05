from abc import abstractmethod
from typing import Any, List, Optional, Type

from emo.assets.domain.entity.asset import Asset
from emo.shared.domain import AssetId, DomainRepository, UserId


class AssetFileRepository(DomainRepository):
    # TODO move me to implementation/infra.
    #  This detail does not need to be here
    def create(self, asset: Asset, file: bytes):
        raise NotImplementedError

    def update(self, asset: Asset, file: bytes):
        raise NotImplementedError

    def copy(self, source: Asset, target: Asset):
        raise NotImplementedError

    def move(self, source: Asset, target: Asset):
        raise NotImplementedError

    def delete(self, asset: Asset):
        raise NotImplementedError


class AssetRepository(DomainRepository):
    def __init__(self, file_repository: Type[AssetFileRepository]):
        pass

    @abstractmethod
    def all(self, owner: UserId) -> List[Asset]:
        """
        Returns all the assets this user has access to
        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def create(self, asset: Asset) -> Any:
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, id: AssetId) -> Optional[Asset]:
        raise NotImplementedError

    @abstractmethod
    def find_by_ids(self, ids: List[AssetId]) -> List[Asset]:
        raise NotImplementedError

    @abstractmethod
    def find_by_ownerid(self, uid: UserId) -> List[Asset]:
        raise NotImplementedError

    @abstractmethod
    def delete_by_id(self, id: AssetId):
        raise NotImplementedError
