from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from emo.users.domain.entity.users import User
from emo.users.domain.entity.user_repository import UserRepository
from emo.users.infrastructure.fastapi.v1.schemas.users import *
from emo.users.infrastructure.dependencies import get_current_active_user, user_repository, event_bus
from emo.shared.domain.usecase import EventPublisher
from emo.users.infrastructure.fastapi.v1.schemas.users import UserCreate
from emo.users.domain.usecase.register_user import RegisterUser
from emo.shared.infrastructure.fastapi.schema_utils import to_pydantic_model
from emo.settings import settings

router = APIRouter(
    responses={404: {"description": "Not found"}},
    prefix=settings.API_USER_PATH,
    tags=[settings.API_USER_PATH.replace('/', '')],
)


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return to_pydantic_model(current_user, UserResponse)


@router.get("/", response_model=List[UserResponse])
async def get_all_users(repo: UserRepository = Depends(user_repository)):
    # TODO change me. Allow only admins
    return [to_pydantic_model(u, UserResponse) for u in repo.all()]


@router.post("/", response_model=UserResponse)
async def register_user(
        *,
        repo: UserRepository = Depends(user_repository),
        bus: EventPublisher = Depends(event_bus),
        new_user: UserCreate
):
    try:
        uc = RegisterUser(repository=repo, message_bus=bus, **new_user.__dict__)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    try:
        uc.execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    return to_pydantic_model(uc._entity, UserResponse)
