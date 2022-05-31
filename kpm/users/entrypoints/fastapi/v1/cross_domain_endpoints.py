"""
This file contains the cross domain endpoints (info needed from assets
and user domains as of now)
"""

from fastapi import APIRouter, Depends, status

from kpm.settings import settings as s
from kpm.shared.entrypoints.auth_jwt import AccessToken
from kpm.shared.entrypoints.fastapi.dependencies import (
    asset_rel_view,
    message_bus,
    user_view,
)
from kpm.shared.entrypoints.fastapi.jwt_dependencies import get_access_token
from kpm.shared.entrypoints.fastapi.schemas import HTTPError
from kpm.shared.service_layer.message_bus import MessageBus

router = APIRouter(
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Not found"},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
        status.HTTP_403_FORBIDDEN: {"model": HTTPError},
    },
)


@router.get(
    s.API_ME.concat("pending-actions").path(),
    responses={
        status.HTTP_200_OK: {},
    },
)
async def my_pending_actions(
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
    legacy=Depends(asset_rel_view),
    users=Depends(user_view),
):
    keeps_pending = users.pending_keeps(token.subject, bus)
    incoming_legacy = legacy.pending(token.subject, bus)

    return {
        "keeps": keeps_pending,
        "legacy": incoming_legacy,
    }
