from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination import Page, Params, paginate

from kpm.settings import settings
from kpm.shared.infra.fastapi.schema_utils import to_pydantic_model
from kpm.shared.infra.fastapi.schemas import HTTPError
from kpm.users.domain.entity.user_repository import UserRepository
from kpm.users.domain.entity.users import User
from kpm.users.domain.usecase.exceptions import (
    EmailAlreadyExistsException, UsernameAlreadyExistsException)
from kpm.users.domain.usecase.register_user import RegisterUser
from kpm.users.infra.dependencies import (get_current_active_user,
                                          user_repository)
from kpm.users.infra.fastapi.v1.schemas.users import UserCreate, UserResponse

router = APIRouter(
    responses={404: {"description": "Not found"}},
    **settings.API_USER_PATH.dict(),
)


@router.get(
    "/me",
    responses={
        status.HTTP_200_OK: {"model": UserResponse},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
    },
)
async def my_user(current_user: User = Depends(get_current_active_user)):
    return to_pydantic_model(current_user, UserResponse)


@router.get(
    "",
    responses={status.HTTP_200_OK: {"model": Page[UserResponse]}},
    tags=["admin"],
)
async def get_all_users(
    params: Params = Depends(), repo: UserRepository = Depends(user_repository)
):
    # TODO change me. Allow only admins
    return paginate(
        [to_pydantic_model(u, UserResponse) for u in repo.all()], params
    )


@router.post(
    "",
    responses={
        status.HTTP_201_CREATED: {"model": UserResponse},
        status.HTTP_400_BAD_REQUEST: {"model": HTTPError},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": HTTPError},
    },
)
async def register_user(
    *, repo: UserRepository = Depends(user_repository), new_user: UserCreate
):
    try:
        uc = RegisterUser(repository=repo, **new_user.__dict__)
    except (Exception, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    try:
        uc.execute()
    except (EmailAlreadyExistsException, UsernameAlreadyExistsException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.msg
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    return to_pydantic_model(uc._entity, UserResponse)
