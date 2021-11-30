from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from kpm.settings import settings
from kpm.shared.infra.dependencies import create_jwt_token
from kpm.shared.infra.fastapi.schemas import TokenData
from kpm.shared.security import salt_password, verify_password
from kpm.users.domain.entity.user_repository import UserRepository
from kpm.users.domain.entity.users import User
from kpm.users.domain.usecase.query_user import QueryUser
from kpm.users.infra.dependencies import user_repository
from kpm.users.infra.fastapi.v1.schemas.token import LoginResponse

router = APIRouter(
    responses={404: {"description": "Not found"}},
    **settings.API_TOKEN.dict(),
)


def authenticate_user(
    q: QueryUser, username: str, password: str
) -> Optional[User]:
    user = q.fetch_by_email(username)
    if not user:
        return None
    if not verify_password(
        salt_password(password, user.salt), user.password_hash
    ):
        return None
    return user


@router.post("", response_model=LoginResponse)
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
    token_data = TokenData(user_id=user.id.id, disabled=user.disabled)
    access_token = create_jwt_token(
        data=token_data.dict(), expires_delta=at_expires
    )
    return LoginResponse(
        user_id=user.id.id, access_token=access_token, token_type="bearer"
    )
