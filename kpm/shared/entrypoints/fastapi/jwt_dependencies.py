from datetime import timedelta
from typing import Optional, Type, TypeVar

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from starlette import status

import kpm.shared.entrypoints.fastapi.exceptions as ex
from kpm.settings import settings
from kpm.settings import settings as cfg
from kpm.shared.domain.time_utils import now_utc
from kpm.shared.entrypoints.auth_jwt import (
    AccessToken,
    RefreshToken,
    from_token,
)
from kpm.shared.log import logger

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=settings.API_V1.concat("/login").path()
)

T = TypeVar("T")


def decode_token(token: str, cls: Type[T]) -> T:
    payload = jwt.decode(
        token, cfg.JWT_SECRET_KEY, algorithms=[cfg.JWT_ALGORITHM]
    )
    return cls(**payload)


async def get_access_token(t: str = Depends(oauth2_scheme)) -> AccessToken:
    try:
        token = from_token(t)
        if token.is_access() and token.is_valid():
            return token
    except Exception as e:
        logger.warning("Exception validating JWT token " + str(e))

    raise ex.TOKEN_ER


async def get_fresh_token(token: AccessToken = Depends(get_access_token)) -> AccessToken:
    if token.is_fresh():
        return token
    else:
        raise ex.TOKEN_STALE


async def get_admin_token(
    t: AccessToken = Depends(get_access_token),
) -> AccessToken:
    if "admin" not in t.scopes:
        raise ex.FORBIDDEN_GENERIC
    else:
        return t


async def get_refresh_token(t: str = Depends(oauth2_scheme)) -> RefreshToken:
    token = from_token(t)
    if token.is_refresh() and token.is_valid():
        return token
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_jwt_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = now_utc() + expires_delta
    else:
        expire = now_utc() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt
