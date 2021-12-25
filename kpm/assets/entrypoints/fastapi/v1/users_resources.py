from fastapi import APIRouter, Depends, status
from fastapi_pagination import Page, Params, paginate

import kpm.assets.adapters.memrepo.views_asset_release as views_releases
from kpm.assets.adapters.memrepo import views_asset
from kpm.assets.entrypoints.fastapi.dependencies import message_bus
from kpm.assets.entrypoints.fastapi.v1.assets import asset_to_response
from kpm.assets.entrypoints.fastapi.v1.schemas import (
    AssetResponse,
    ReleaseResponse,
)
from kpm.settings import settings
from kpm.shared.entrypoints.auth_jwt import AccessToken
from kpm.shared.entrypoints.fastapi.jwt_dependencies import get_access_token
from kpm.shared.entrypoints.fastapi.schemas import HTTPError
from kpm.shared.service_layer.message_bus import MessageBus

router = APIRouter(
    responses={404: {"description": "Not found"}},
    prefix=settings.API_USER_PATH.prefix,
)


@router.get(
    "/me" + settings.API_ASSET_PATH.prefix,
    tags=settings.API_ASSET_PATH.tags,
    responses={
        status.HTTP_200_OK: {"model": Page[AssetResponse]},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
    },
)
async def get_user_assets(
    params: Params = Depends(),
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
):
    assets = views_asset.find_by_ownerid(token.subject, bus=bus)
    return paginate([asset_to_response(a, token) for a in assets], params)


@router.get(
    "/me" + settings.API_RELEASE.prefix,
    tags=settings.API_RELEASE.tags,
    responses={
        status.HTTP_200_OK: {"model": Page[ReleaseResponse]},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
    },
)
async def get_user_releases(
    params: Params = Depends(),
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
):
    return paginate(
        [
            ReleaseResponse(**r)
            for r in views_releases.get_releases(token.subject, bus=bus)
        ],
        params,
    )
