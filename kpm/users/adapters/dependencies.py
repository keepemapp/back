from fastapi import Depends, HTTPException, status

import kpm.shared.entrypoints.fastapi.exceptions as ex
from kpm.shared.entrypoints.auth_jwt import AccessToken
from kpm.shared.entrypoints.fastapi.dependencies import message_bus
from kpm.shared.entrypoints.fastapi.jwt_dependencies import get_access_token
from kpm.shared.service_layer.message_bus import MessageBus
from kpm.users.adapters.memrepo import views
from kpm.users.domain.model import User


async def get_current_user(
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user = views.by_id(token.subject, bus)
    if not user:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.is_disabled():
        raise ex.USER_INACTIVE
    return current_user
