from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt

from emo.settings import settings
from emo.shared.security import salt_password, verify_password
from emo.users.domain.entity.user_repository import UserRepository
from emo.users.domain.entity.users import User
from emo.users.domain.usecase.query_user import QueryUser
from emo.users.infrastructure.dependencies import user_repository
from emo.users.infrastructure.fastapi.v1.schemas.token import Token

router = APIRouter(
    responses={404: {"description": "Not found"}},
    **settings.API_TOKEN.dict(),
)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
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


def authenticate_user(q: QueryUser, username: str, password: str) \
        -> Optional[User]:
    user = q.fetch_by_email(username)
    if not user:
        return None
    if not verify_password(salt_password(password, user.salt),
                           user.password_hash):
        return None
    return user


@router.post("/", response_model=Token)
async def login_for_access_token(
    repo: UserRepository = Depends(user_repository),
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    q = QueryUser(repository=repo)
    user = authenticate_user(q, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    at_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id.id}, expires_delta=at_expires
    )
    return Token(access_token=access_token, token_type="bearer")
