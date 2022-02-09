import os
import pickle
from typing import Dict, List, Optional

from kpm.settings import settings
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import RootAggState, UserId
from kpm.users.domain.model import Keep, User
from kpm.users.domain.repositories import KeepRepository, UserRepository

Users = Dict[str, User]


class MemoryPersistedUserRepository(UserRepository):
    """In memory repository for Users with file storage.
    Don't use this in production
    """

    def __init__(
        self,
        dbfile=os.path.join(settings.DATA_FOLDER, "usersrepo.pk"),
    ):
        super().__init__()
        self.DB_FILE = dbfile
        self._users: Users = self.__startup_db()

    def all(self) -> List[User]:
        return list(self._users.values())

    def get(self, uid: UserId) -> Optional[User]:
        return self._users.get(str(uid.id))

    def create(self, user: User):
        self._users[user.id.id] = user
        self._seen.add(user)

    def update(self, user: User):
        self._users[user.id.id] = user
        self._seen.add(user)

    def commit(self):
        self.__write_file()

    def exists_email(self, email: str) -> bool:
        def is_email_equals(email1: str, email2: str):
            if "@gmail" in email1:
                return (
                    email1.replace(".", "").lower()
                    == email2.replace(".", "").lower()
                )
            else:
                return email1.lower() == email2.lower()

        return any(is_email_equals(u.email, email) for u in self.all())

    def exists_username(self, username: str) -> bool:
        return any(u.username == username for u in self.all())

    def empty(self) -> bool:
        return True if not self._users else False

    def __write_file(self):
        with open(self.DB_FILE, "wb") as f:
            pickle.dump(self._users, f)

    def __startup_db(self) -> Users:
        if os.path.exists(self.DB_FILE):
            with open(self.DB_FILE, "rb") as f:
                r = pickle.load(f)
            return r
        return {}


class KeepMemoryRepository(KeepRepository):
    def __init__(
        self,
        dbfile=os.path.join(settings.DATA_FOLDER, "keepsrepo.pk"),
    ):
        super().__init__()
        self.DB_FILE = dbfile
        self._keeps: List[Keep] = self.__startup_db()

    def all(self, user: UserId = None) -> List[Keep]:
        if user:
            return list(
                filter(
                    lambda k: user in (k.requester, k.requested), self._keeps
                )
            )
        else:
            return self._keeps

    def get(self, kid: DomainId) -> Keep:
        return next(filter(lambda k: k.id == kid, self._keeps), None)

    def put(self, k: Keep):
        self._keeps.append(k)

    def commit(self):
        self.__write_file()

    def __startup_db(self) -> List[Keep]:
        if os.path.exists(self.DB_FILE):
            with open(self.DB_FILE, "rb") as f:
                r = pickle.load(f)
            return r
        return []

    def exists(
        self, user1: UserId, user2: UserId, all_states: bool = False
    ) -> bool:
        if user1.id == user2.id:
            return True
        for k in self._keeps:
            cond1 = k.requester in (user1, user2)
            cond2 = k.requested in (user1, user2)
            cond3 = all_states or k.state == RootAggState.ACTIVE
            if cond1 and cond2 and cond3:
                return True
        return False

    def __write_file(self):
        with open(self.DB_FILE, "wb") as f:
            pickle.dump(self._keeps, f)
