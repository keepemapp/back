from abc import abstractmethod
from typing import List, Optional

from kpm.shared.domain.model import UserId
from kpm.shared.domain.repository import DomainRepository
from kpm.users.domain.entity.users import User


class UserRepository(DomainRepository):
    # TODO return of users should not have the password and salt
    # Those should only be returned if you cal a get_credentials() specifically
    @abstractmethod
    def all(self) -> List[User]:
        raise NotImplementedError

    @abstractmethod
    def get(self, uid: UserId) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    def exists_email(self, email: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def exists_username(self, email: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def create(self, user: User):
        raise NotImplementedError

    @abstractmethod
    def update(self, user: User):
        raise NotImplementedError

    @abstractmethod
    def empty(self) -> bool:
        raise NotImplementedError
