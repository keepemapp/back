from typing import List, Optional, Dict
import pickle
import os

from emo.shared.domain import UserId
from emo.users.domain.entity.user_repository import UserRepository
from emo.users.domain.entity.users import User

Users = Dict[str, User]


class MemoryPersistedUserRepository(UserRepository):
    """
    In memory repository for Users. Don't use this in production
    """

    DB_FILE = '../data/usersrepo.pk'

    def __init__(self):
        self._users: Users = self.__startup_db()

    def all(self) -> List[User]:
        return list(self._users.values())

    def get(self, uid: UserId) -> Optional[User]:
        return self._users.get(str(uid.id))

    def create(self, user: User):
        self._users[user.id.id] = user
        self.__write_file()

    def update(self, user: User):
        self._users[user.id.id] = user
        self.__write_file()

    def exists_email(self, email: str) -> bool:
        return any(u.email == email for u in self.all())

    def exists_username(self, username: str) -> bool:
        return any(u.username == username for u in self.all())

    def __write_file(self):
        with open(self.DB_FILE, 'wb') as f:
            pickle.dump(self._users, f)

    def __startup_db(self) -> Users:
        if os.path.exists(self.DB_FILE):
            with open(self.DB_FILE, 'rb') as f:
                r = pickle.load(f)
            return r
        return {}
