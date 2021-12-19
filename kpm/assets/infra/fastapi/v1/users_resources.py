from typing import List

from fastapi import APIRouter, Depends, status

import kpm.assets.infra.memrepo.views_asset_release as views_releases
from kpm.assets.infra.dependencies import message_bus
from kpm.assets.infra.fastapi.v1.assets import asset_to_response
from kpm.assets.infra.fastapi.v1.schemas import AssetResponse
from kpm.assets.infra.fastapi.v1.schemas.releases import ReleaseResponse
from kpm.assets.infra.memrepo import views_asset
from kpm.settings import settings
from kpm.shared.domain.usecase.message_bus import MessageBus
from kpm.shared.infra.auth_jwt import AccessToken
from kpm.shared.infra.dependencies import get_access_token
from kpm.shared.infra.fastapi.schemas import HTTPError

router = APIRouter(
    responses={404: {"description": "Not found"}},
    prefix=settings.API_USER_PATH.prefix,
)


@router.get(
    "/me" + settings.API_ASSET_PATH.prefix,
    tags=settings.API_ASSET_PATH.tags,
    responses={
        status.HTTP_200_OK: {"model": List[AssetResponse]},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
    },
)
async def get_user_assets(
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
):
    assets = views_asset.find_by_ownerid(token.subject, bus=bus)
    return [asset_to_response(a, token) for a in assets]


@router.get(
    "/me" + settings.API_RELEASE.prefix,
    tags=settings.API_RELEASE.tags,
    responses={
        status.HTTP_200_OK: {"model": List[ReleaseResponse]},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
    },
)
async def get_user_releases(
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
):
    return [
        ReleaseResponse(**r)
        for r in views_releases.get_releases(token.subject, bus=bus)
    ]
