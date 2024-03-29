from abc import abstractmethod
from typing import List, Optional, Set

from kpm.shared.domain import DomainId
from kpm.shared.domain.model import UserId
from kpm.shared.domain.repository import DomainRepository
from kpm.users.domain.model import Keep, Session, User


class UserRepository(DomainRepository):
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
    def by_email(self, email: str) -> Optional[User]:
        raise NotImplementedError

    @abstractmethod
    def exists_email(self, email: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def exists_username(self, username: str) -> bool:
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
    def exists(
        self, user1: UserId, user2: UserId, all_states: bool = False
    ) -> bool:
        raise NotImplementedError


class SessionRepository(DomainRepository):
    def __init__(self):
        super(SessionRepository, self).__init__()
        self._seen: Set[Session] = set()

    @abstractmethod
    def put(self, s: Session):
        raise NotImplementedError

    @abstractmethod
    def get(
        self, sid: DomainId = None, user: UserId = None, token: str = None
    ) -> List[Session]:
        raise NotImplementedError
