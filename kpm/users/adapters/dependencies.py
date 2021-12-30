from fastapi import Depends, HTTPException, status

import kpm.shared.entrypoints.fastapi.exceptions as ex
from kpm.shared.domain.model import UserId
from kpm.shared.entrypoints.auth_jwt import AccessToken
from kpm.shared.entrypoints.fastapi.jwt_dependencies import get_access_token
from kpm.users.adapters.memrepo.repository import MemoryPersistedUserRepository
from kpm.users.domain.model import User
from kpm.users.domain.repositories import UserRepository
from kpm.users.domain.usecase.query_user import QueryUser


def user_repository() -> UserRepository:
    yield MemoryPersistedUserRepository()


def query_user(repo: UserRepository = Depends(user_repository)) -> QueryUser:
    yield QueryUser(repository=repo)


async def get_current_user(
    token: AccessToken = Depends(get_access_token),
    q: QueryUser = Depends(query_user),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = q.fetch_by_id(UserId(token.subject))
    if not user:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.is_disabled():
        raise ex.USER_INACTIVE
    return current_user
