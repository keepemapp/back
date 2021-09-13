from fastapi import Depends, HTTPException, status

from emo.shared.domain import UserId
from emo.shared.infra.dependencies import get_authorized_token
from emo.shared.infra.fastapi.schemas import TokenData
from emo.users.domain.entity.user_repository import UserRepository
from emo.users.domain.entity.users import User
from emo.users.domain.usecase.query_user import QueryUser
from emo.users.infra.memrepo.repository import MemoryPersistedUserRepository


def user_repository() -> UserRepository:
    yield MemoryPersistedUserRepository()


def query_user(repo: UserRepository = Depends(user_repository)) -> QueryUser:
    yield QueryUser(repository=repo)


async def get_current_user(
    token_data: TokenData = Depends(get_authorized_token),
    q: QueryUser = Depends(query_user),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = q.fetch_by_id(UserId(token_data.user_id))
    if not user:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user"
        )
    return current_user
