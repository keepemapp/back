from typing import Dict, List, Optional

from kpm.shared.domain.model import UserId
from kpm.users.domain.model import User
from kpm.users.domain.repositories import UserRepository

Users = Dict[str, User]


class MemoryUserRepository(UserRepository):
    def __init__(self):
        super().__init__()
        self._users: Users = {}

    def all(self) -> List[User]:
        return list(self._users.values())

    def get(self, uid: UserId) -> Optional[User]:
        return self._users.get(str(uid))

    def create(self, user: User):
        self._users[str(user.id)] = user
        self._seen.add(user)

    def update(self, user: User):
        self._users[str(user.id)] = user
        self._seen.add(user)

    def clean_all(self):
        self._users.clear()

    def exists_email(self, email: str) -> bool:
        return any(u.email == email for u in self.all())

    def exists_username(self, username: str) -> bool:
        return any(u.username == username for u in self.all())

    def empty(self) -> bool:
        return True if not self._users else False
