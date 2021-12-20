import logging
from datetime import datetime, timedelta
from typing import Optional, Type, TypeVar

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from starlette import status

from kpm.settings import settings
from kpm.settings import settings as cfg
from kpm.shared.infra.auth_jwt import AccessToken, RefreshToken, from_token

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=settings.API_V1.concat("/login").path()
)

T = TypeVar("T")

logger = logging.getLogger("kpm")


def decode_token(token: str, cls: Type[T]) -> T:
    payload = jwt.decode(token, cfg.JWT_SECRET_KEY,
                         algorithms=[cfg.JWT_ALGORITHM])
    return cls(**payload)


async def get_access_token(t: str = Depends(oauth2_scheme)) -> AccessToken:
    try:
        token = from_token(t)
        if token.is_access() and token.is_valid():
            return token
    except Exception as e:
        logger.warning("Exception validating JWT token " + str(e))

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


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
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt
