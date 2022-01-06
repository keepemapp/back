from abc import abstractmethod
from typing import List, Optional, Set

from kpm.shared.domain import DomainId
from kpm.shared.domain.model import UserId
from kpm.shared.domain.repository import DomainRepository
from kpm.users.domain.model import User, Keep


class UserRepository(DomainRepository):
    # TODO return of users should not have the password and salt
    # Those should only be returned if you cal a get_credentials() specifically

    def __init__(self):
        super(UserRepository, self).__init__()
        self._seen: Set[User] = set()

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


class KeepRepository(DomainRepository):
    def __init__(self):
        super(KeepRepository, self).__init__()
        self._seen: Set[Keep] = set()

    @abstractmethod
    def put(self, k: Keep):
        raise NotImplementedError

    @abstractmethod
    def all(self, user: UserId = None) -> List[Keep]:
        raise NotImplementedError

    @abstractmethod
    def get(self, kid: DomainId) -> Keep:
        raise NotImplementedError

    @abstractmethod
    def exists(self, user1: UserId, user2: UserId) -> bool:
        raise NotImplementedError
