from typing import List, Optional

from emo.shared.domain.usecase import Query, UserId
from emo.users.domain.entity.user_repository import UserRepository
from emo.users.domain.entity.users import User


class QueryUser(Query):
    def __init__(self, *, repository: UserRepository):
        self.__repository = repository

    def fetch_by_id(self, uid: UserId) -> Optional[User]:
        return self.__repository.get(uid)

    def fetch_by_email(self, email: str) -> Optional[User]:
        return next(
            (u for u in self.__repository.all()
             if u.email.lower() == email.lower()),
            None,
        )

    def fetch_all(self) -> List[User]:
        return self.__repository.all()
