from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination import Page, Params, paginate
from jose import JWTError

import kpm.shared.entrypoints.fastapi.exceptions as ex
import kpm.users.domain.commands as cmds
from kpm.settings import settings as s
from kpm.shared.entrypoints.auth_jwt import AccessToken
from kpm.shared.entrypoints.fastapi.dependencies import message_bus, user_view
from kpm.shared.entrypoints.fastapi.jwt_dependencies import (
    decode_token, get_access_token,
    get_admin_token,
)
from kpm.shared.entrypoints.fastapi.schema_utils import to_pydantic_model
from kpm.shared.entrypoints.fastapi.schemas import HTTPError
from kpm.shared.service_layer.message_bus import MessageBus
from kpm.users.adapters.dependencies import get_current_active_user
from kpm.users.domain.model import (EmailAlreadyExistsException,
                                    MissmatchPasswordException, User,
                                    UserNotFound,
                                    UsernameAlreadyExistsException)
from kpm.users.entrypoints.fastapi.v1.schemas import users as schemas
from kpm.users.entrypoints.fastapi.v1.schemas.users import Reminder, UserRemoval

router = APIRouter(
    responses={404: {"description": "Not found"}},
    tags=s.API_USER_PATH.tags,
)


@router.get(
    s.API_USER_PATH.concat("me").path(),
    deprecated=True,
    responses={
        status.HTTP_200_OK: {"model": schemas.UserResponse},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
    },
)
@router.get(
    s.API_ME.path(),
    responses={
        status.HTTP_200_OK: {"model": schemas.UserResponse},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
    },
)
async def my_user(current_user: User = Depends(get_current_active_user)):
    """Returns user information"""
    return to_pydantic_model(current_user, schemas.UserResponse)


@router.get(
    s.API_USER_PATH.path(),
    responses={status.HTTP_200_OK: {"model": Page[schemas.UserResponse]}},
    tags=["admin"],
)
async def get_all_users(
    params: Params = Depends(),
    bus: MessageBus = Depends(message_bus),
    _: AccessToken = Depends(get_admin_token),
    views=Depends(user_view),
):
    """Returns all users"""
    try:
        return paginate(
            [
                to_pydantic_model(u, schemas.UserResponse)
                for u in views.all_users(bus)
            ],
            params,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.put(
    s.API_USER_PATH.concat("{user_id}", "activate").path(),
    responses={status.HTTP_200_OK: {}},
    tags=["admin"],
)
async def activate_user_by_admin(
    user_id: str,
    bus: MessageBus = Depends(message_bus),
    _: AccessToken = Depends(get_admin_token),
):
    """Endpoint to activate a user. If user is already active does nothing."""
    try:
        bus.handle(cmds.ActivateUser(user_id=user_id))
    except UserNotFound:
        raise ex.NOT_FOUND
    return


@router.get(
    s.API_USER_PATH.concat("activate").path(),
    responses={status.HTTP_200_OK: {}},
)
async def activate_user(
    activation_token: str,
    bus: MessageBus = Depends(message_bus),
):
    """Endpoint to activate a user. If user is already active does nothing."""
    try:
        token = decode_token(activation_token, dict)
        user_id = token.get("user_id", "NON EXIST USER ID")
        bus.handle(cmds.ActivateUser(user_id=user_id))
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate authorizer token",
        )
    except UserNotFound:
        raise ex.NOT_FOUND
    return "User Activated. You can Log in in your app"


@router.post(
    s.API_USER_PATH.path(),
    responses={
        status.HTTP_201_CREATED: {"model": schemas.UserResponse},
        status.HTTP_400_BAD_REQUEST: {"model": HTTPError},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": HTTPError},
    },
    status_code=201,
)
def register_user(
    new_user: schemas.UserCreate,
    bus: MessageBus = Depends(message_bus),
    views=Depends(user_view),
):
    referred_by = None
    if new_user.referral_code:
        referred_by = views.id_from_referral(new_user.referral_code, bus)
        if not referred_by:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Referral code erroneous or not found",
            )
    cmd = cmds.RegisterUser(
        username=new_user.username,
        email=new_user.email,
        password=new_user.password,
        referred_by=referred_by,
    )
    try:
        bus.handle(cmd)
    except ValueError as e:
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
            detail=str(type(e)),
        )
    return to_pydantic_model(
        views.by_id(cmd.user_id, bus), schemas.UserResponse
    )


@router.patch(
    "/me/change-password",
    responses={
        status.HTTP_200_OK: {},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
        status.HTTP_403_FORBIDDEN: {"model": HTTPError},
    },
)
async def change_password(
    pwd_change: schemas.PasswordUpdate,
    bus: MessageBus = Depends(message_bus),
    token: AccessToken = Depends(get_access_token),
):
    """Endpoint to change password of the user."""

    try:
        bus.handle(
            cmds.UpdateUserPassword(user_id=token.subject, **pwd_change.dict())
        )
    except UserNotFound:
        raise ex.NOT_FOUND
    except MissmatchPasswordException:
        raise ex.USER_CREDENTIALS_ER
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    return


@router.patch(
    "/me",
    responses={
        status.HTTP_200_OK: {},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
    },
)
async def update_user_attributes(
    updates: schemas.UserUpdate,
    bus: MessageBus = Depends(message_bus),
    token: AccessToken = Depends(get_access_token),
):
    """Updates user attributes."""

    try:
        bus.handle(cmds.UpdateUser(user_id=token.subject, **updates.dict()))
    except UserNotFound:
        raise ex.NOT_FOUND
    return


@router.delete(
    s.API_USER_PATH.concat("{user_id}").path(),
    responses={status.HTTP_200_OK: {}},
    tags=["admin"],
)
async def remove_user(
    user_id: str,
    reason: UserRemoval,
    bus: MessageBus = Depends(message_bus),
    token: AccessToken = Depends(get_admin_token),
):
    """Endpoint to remove an user and all of its items"""
    try:
        bus.handle(
            cmds.RemoveUser(
                user_id=user_id, deleted_by=token.subject, reason=reason.reason
            )
        )
    except UserNotFound:
        raise ex.NOT_FOUND
    return


@router.post(
    s.API_USER_PATH.concat("me", "reminders").path(),
    responses={
        status.HTTP_201_CREATED: {},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
    },
    status_code=201,
)
async def add_reminders(
    reminders: List[Reminder],
    bus: MessageBus = Depends(message_bus),
    token: AccessToken = Depends(get_access_token),
):
    """Endpoint to add reminders of the user

    **IMPORTANT**: A reminder is considered unique if it has the same
    `title` and `time`.
    """
    try:
        for r in reminders:
            payload = r.__dict__
            payload = {k: v for k, v in payload.items() if v is not None}
            bus.handle(cmds.AddUserReminder(user_id=token.subject,
                                            **payload))
    except UserNotFound:
        raise ex.NOT_FOUND
    return


@router.get(
    s.API_USER_PATH.concat("me", "reminders").path(),
    responses={
        status.HTTP_200_OK: {},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
    },
)
async def get_reminders(
    bus: MessageBus = Depends(message_bus),
    token: AccessToken = Depends(get_access_token),
    views=Depends(user_view),
):
    """Endpoint to list the reminders of the user"""
    try:
        res = views.get_user_reminders(user_id=token.subject, bus=bus)
    except UserNotFound:
        raise ex.NOT_FOUND
    return res


@router.delete(
    s.API_USER_PATH.concat("me", "reminders").path(),
    responses={status.HTTP_200_OK: {}},
)
async def remove_reminder(
    reminders: List[Reminder],
    bus: MessageBus = Depends(message_bus),
    token: AccessToken = Depends(get_access_token),
):
    """Endpoint to remove the reminders of the user"""
    try:
        for r in reminders:
            bus.handle(cmds.RemoveUserReminder(
                user_id=token.subject,
                title=r.title,
                time=r.time
            ))
    except UserNotFound:
        raise ex.NOT_FOUND
    return