from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination import Page, Params, paginate

import kpm.shared.entrypoints.fastapi.exceptions as ex
import kpm.users.domain.commands as cmds
from kpm.settings import settings as s
from kpm.shared.entrypoints.auth_jwt import AccessToken
from kpm.shared.entrypoints.fastapi.dependencies import message_bus
from kpm.shared.entrypoints.fastapi.jwt_dependencies import get_admin_token
from kpm.shared.entrypoints.fastapi.schema_utils import to_pydantic_model
from kpm.shared.entrypoints.fastapi.schemas import HTTPError
from kpm.shared.service_layer.message_bus import MessageBus
from kpm.users.adapters.dependencies import get_current_active_user
from kpm.users.adapters.memrepo import views
from kpm.users.domain.model import (EmailAlreadyExistsException, User,
                                    UsernameAlreadyExistsException)
from kpm.users.entrypoints.fastapi.v1.schemas.users import (UserCreate,
                                                            UserResponse)

router = APIRouter(
    responses={404: {"description": "Not found"}},
    tags=s.API_USER_PATH.tags,
)


@router.get(
    s.API_USER_PATH.concat("me").path(),
    deprecated=True,
    responses={
        status.HTTP_200_OK: {"model": UserResponse},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
    },
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
    s.API_USER_PATH.path(),
    responses={status.HTTP_200_OK: {"model": Page[UserResponse]}},
    tags=["admin"],
)
async def get_all_users(
    params: Params = Depends(),
    bus: MessageBus = Depends(message_bus),
    _: AccessToken = Depends(get_admin_token),
):
    return paginate(
        [to_pydantic_model(u, UserResponse) for u in views.all_users(bus)],
        params,
    )


@router.put(
    s.API_USER_PATH.concat("{user_id}", "activate").path(),
    responses={status.HTTP_200_OK: {}},
    tags=["admin"],
)
async def activate_user(
    user_id: str,
    bus: MessageBus = Depends(message_bus),
    _: AccessToken = Depends(get_admin_token),
):
    """Endpoint to activate a user. If user is already active does nothing."""
    try:
        bus.handle(cmds.ActivateUser(user_id=user_id))
    except KeyError:
        raise ex.NOT_FOUND
    return


@router.post(
    s.API_USER_PATH.path(),
    responses={
        status.HTTP_201_CREATED: {"model": UserResponse},
        status.HTTP_400_BAD_REQUEST: {"model": HTTPError},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": HTTPError},
    },
)
def register_user(
    new_user: UserCreate, bus: MessageBus = Depends(message_bus)
):
    cmd = cmds.RegisterUser(
        username=new_user.username,
        email=new_user.email,
        password=new_user.password,
    )
    try:
        bus.handle(cmd)
    except (Exception, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except (EmailAlreadyExistsException, UsernameAlreadyExistsException) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=e.msg
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    return to_pydantic_model(views.by_id(cmd.user_id, bus), UserResponse)
