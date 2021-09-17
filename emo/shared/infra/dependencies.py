from datetime import datetime, timedelta
from typing import Optional, Type, TypeVar

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from starlette import status

from emo.settings import settings
from emo.settings import settings as cfg
from emo.shared.domain.usecase import EventPublisher
from emo.shared.infra.fastapi.schemas import TokenData
from emo.shared.infra.memrepo.message_bus import NoneEventPub


def event_bus() -> EventPublisher:
    yield NoneEventPub()


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=settings.API_V1.concat(settings.API_TOKEN).prefix
)

T = TypeVar("T")


def decode_token(token: str, cls: Type[T]) -> T:
    payload = jwt.decode(token, cfg.SECRET_KEY, algorithms=[cfg.ALGORITHM])
    return cls(**payload)


async def get_authorized_token(
    token: str = Depends(oauth2_scheme),
) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token_data = decode_token(token, TokenData)
        if not token_data.user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return token_data


async def get_active_user_token(
    token: TokenData = Depends(get_authorized_token),
) -> TokenData:
    inactive_user_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Operation forbidden for inactive users",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token.disabled:
        raise inactive_user_exception
    return token


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
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt
