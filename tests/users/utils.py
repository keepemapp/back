from typing import Dict, List, Optional

from kpm.shared.domain import DomainId
from kpm.shared.domain.model import RootAggState, UserId
from kpm.users.domain.model import Keep, User
from kpm.users.domain.repositories import KeepRepository, UserRepository

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


class TestKeepRepository(KeepRepository):
    def __init__(self):
        super().__init__()
        self._keeps: Dict[str, Keep] = {}

    def all(self, user: UserId = None) -> List[Keep]:
        if user:
            return list(
                filter(
                    lambda k: user in (k.requester, k.requested),
                    self._keeps.values(),
                )
            )
        else:
            return list(self._keeps.values())

    def get(self, kid: DomainId) -> Keep:
        return self._keeps[kid.id]

    def put(self, k: Keep):
        print("adding keep", k)
        self._keeps[k.id.id] = k

    def exists(
        self, user1: UserId, user2: UserId, all_states: bool = False
    ) -> bool:
        if user1.id == user2.id:
            return True
        for k in self._keeps.values():
            cond1 = k.requester in (user1, user2)
            cond2 = k.requested in (user1, user2)
            cond3 = all_states or k.state == RootAggState.ACTIVE
            if cond1 and cond2 and cond3:
                return True
        return False
