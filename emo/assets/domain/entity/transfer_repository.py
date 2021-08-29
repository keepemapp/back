from abc import abstractmethod
from typing import Any, List, Optional

from emo.assets.domain.entity.transfer import Transfer
from emo.shared.domain import DomainRepository, TransferId, UserId


class TransferRepository(DomainRepository):
    @abstractmethod
    def all(self, owner: UserId) -> List[Transfer]:
        """
        Returns all the assets this user has access to
        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def create(self, transfer: Transfer) -> Any:
        raise NotImplementedError

    @abstractmethod
    def delete(self, transfer: TransferId) -> Any:
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, owner: UserId, id: TransferId) -> Optional[Transfer]:
        raise NotImplementedError

    @abstractmethod
    def find_by_ids(self, owner: UserId, ids: List[TransferId]) \
            -> List[Transfer]:
        raise NotImplementedError
