from abc import abstractmethod
from typing import List, Any, Optional

from emo.shared.domain import TransferId, DomainRepository, UserId
from emo.domain.entity.transfer import Transfer


class TransferRepository(DomainRepository):

    @abstractmethod
    def all(self,  owner: UserId) -> List[Transfer]:
        """
        Returns all the assets this user has access to
        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def create(self, transfer: Transfer) -> Any:
        raise NotImplementedError

    @abstractmethod
    def find_by_id(self, owner: UserId, id: TransferId) -> Optional[Transfer]:
        raise NotImplementedError

    @abstractmethod
    def find_by_ids(self, owner: UserId, ids: List[TransferId]) -> List[Transfer]:
        raise NotImplementedError
