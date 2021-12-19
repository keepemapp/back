from fastapi import Depends, HTTPException, status

from kpm.shared.domain import UserId
from kpm.shared.infra.auth_jwt import AccessToken
from kpm.shared.infra.dependencies import get_access_token
from kpm.shared.infra.fastapi.exceptions import UNAUTHORIZED_GENERIC
from kpm.users.domain.entity.user_repository import UserRepository
from kpm.users.domain.entity.users import User
from kpm.users.domain.usecase.query_user import QueryUser
from kpm.users.infra.memrepo.repository import MemoryPersistedUserRepository


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
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user"
        )
    return current_user


async def get_admin_user(
    token: AccessToken = Depends(get_access_token),
    user: User = Depends(get_current_user),
):
    if token.is_valid(scope="admin") and token.is_fresh():
        return user
    else:
        raise UNAUTHORIZED_GENERIC
