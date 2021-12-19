import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from kpm.settings import settings as s
from kpm.shared.domain import UserId
from kpm.shared.infra.auth_jwt import AccessToken, RefreshToken
from kpm.shared.infra.dependencies import get_refresh_token
from kpm.shared.security import salt_password, verify_password
from kpm.users.domain.entity.user_repository import UserRepository
from kpm.users.domain.entity.users import User
from kpm.users.domain.usecase.query_user import QueryUser
from kpm.users.infra.dependencies import user_repository
from kpm.users.infra.fastapi.v1.schemas.token import LoginResponse

router = APIRouter(
    responses={404: {"description": "Not found"}}, tags=["auth"]
)

logger = logging.getLogger("kpm")


def check_user(user: Optional[User], password: str):
    """Validates user and its password"""
    unauth_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not user:
        raise unauth_exception

    salted_pwd = salt_password(password, user.salt)
    password_is_valid = verify_password(salted_pwd, user.password_hash)

    if password_is_valid:
        logger.info(f"User '{user.id.id}' correctly authenticated")
        return user
    else:
        logger.info(f"Auth failure for user '{user.id.id}'")
        raise unauth_exception


def authenticate_by_email(
    repo: UserRepository, username: str, password: str
) -> Optional[User]:
    logger.info(f"Trying to authenticate email '{username}'")
    q = QueryUser(repository=repo)
    user = q.fetch_by_email(username)
    return check_user(user, password)


def authenticate_by_id(
    repo: UserRepository, user_id: str, password: str
) -> Optional[User]:
    logger.info(f"Trying to authenticate user id '{user_id}'")
    q = QueryUser(repository=repo)
    user = q.fetch_by_id(UserId(user_id))
    return check_user(user, password)


@router.post(s.API_TOKEN.path(), deprecated=True)
async def login_token(
    repo: UserRepository = Depends(user_repository),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    Deprecated. Please use `/login`
    """
    return await login_for_access_token(repo, form_data)


@router.post("/login", response_model=LoginResponse)
async def login_for_access_token(
    repo: UserRepository = Depends(user_repository),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """
    With credentials, creates new access and refresh tokens
    """
    user = authenticate_by_email(repo, form_data.username, form_data.password)

    access_token = AccessToken(subject=user.id.id, scopes=[], fresh=True)
    # TODO not create a new refresh token if one already exists
    # Check https://docs.microsoft.com/en-us/linkedin/shared/authentication/programmatic-refresh-tokens # noqa: E501
    refresh_token = RefreshToken(subject=user.id.id, scopes=[])

    return LoginResponse(
        user_id=user.id.id,
        access_token=access_token.to_token(),
        refresh_token=refresh_token.to_token(),
        access_token_expires=access_token.exp_time,
        refresh_token_expires=refresh_token.exp_time,
    )


@router.post("/refresh")
async def refresh_access_token(
    repo: UserRepository = Depends(user_repository),
    token: RefreshToken = Depends(get_refresh_token),
):
    """
    Refreshes token. This will generate a new access token however it will
    not be fresh since we don't validate user credentials.
    Can't be used for sensitive/administrative endpoints

    For accessing /refresh endpoint remember to **change access_token**
    *with refresh_token* in the header `Authorization: Bearer <refresh_token>`
    """
    q = QueryUser(repository=repo)
    user = q.fetch_by_id(UserId(token.subject))

    scopes = token.scopes  # Intersect with current user permissions
    access_token = AccessToken(subject=user.id.id, scopes=scopes, fresh=False)
    return {
        "access_token": access_token,
        "access_token_expires": access_token.exp_time,
    }
