from typing import List, Optional, Dict

from emo.shared.domain import UserId
from emo.users.domain.entity.user_repository import UserRepository
from emo.users.domain.entity.users import User

Users = Dict[str, User]


class MemoryUserRepository(UserRepository):
    """
    In memory repository for Users. Don't use this in production
    """
    _users: Users = {}

    def all(self) -> List[User]:
        return list(self._users.values())

    def get(self, uid: UserId) -> Optional[User]:
        return self._users.get(str(uid.id))

    def create(self, user: User):
        self._users[user.id.id] = user

    def update(self, user: User):
        self._users[user.id.id] = user
