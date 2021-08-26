from fastapi.security import OAuth2PasswordBearer

from emo.users.domain.entity.user_repository import UserRepository
from emo.users.infrastructure.memory.repository import MemoryPersistedUserRepository

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from emo.settings import settings as cfg

from emo.shared.domain import UserId
from emo.shared.domain.usecase import EventPublisher
from emo.users.domain.entity.users import User
from emo.users.domain.usecase.query_user import QueryUser
from emo.users.domain.usecase.register_user import RegisterUser
from emo.users.infrastructure.fastapi.v1.schemas.token import TokenData
from emo.users.infrastructure.memory.message_bus import NoneEventPub
from emo.settings import settings


def user_repository() -> UserRepository:
    yield MemoryPersistedUserRepository()


def event_bus() -> EventPublisher:
    yield NoneEventPub()


def query_user(repo: UserRepository = Depends(user_repository)) -> QueryUser:
    yield QueryUser(repository=repo)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.API_V1.concat(settings.API_TOKEN).prefix)


async def get_current_user(token: str = Depends(oauth2_scheme), q: QueryUser = Depends(query_user)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, cfg.SECRET_KEY, algorithms=[cfg.ALGORITHM])
        uid: UserId = UserId(id=payload.get("sub"))
        if uid is None:
            raise credentials_exception
        token_data = TokenData(id=uid)
    except JWTError:
        raise credentials_exception
    user = q.fetch_by_id(token_data.id)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    return current_user
