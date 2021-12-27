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
from kpm.settings import settings as s
from kpm.shared.entrypoints.auth_jwt import AccessToken
from kpm.shared.entrypoints.fastapi.jwt_dependencies import get_access_token
from kpm.shared.entrypoints.fastapi.schemas import HTTPError
from kpm.shared.service_layer.message_bus import MessageBus

router = APIRouter(
    responses={404: {"description": "Not found"},
               status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
               },
)


@router.get(
    s.API_USER_PATH.concat("me", s.API_ASSET_PATH).path(),
    deprecated=True,
    tags=s.API_ASSET_PATH.tags,
    responses={
        status.HTTP_200_OK: {"model": Page[AssetResponse]},
    },
)
@router.get(
    "/me" + s.API_ASSET_PATH.prefix,
    tags=s.API_ASSET_PATH.tags,
    responses={
        status.HTTP_200_OK: {"model": Page[AssetResponse]},
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
    s.API_USER_PATH.concat("me", s.API_RELEASE).path(),
    deprecated=True,
    tags=s.API_RELEASE.tags,
    responses={
        status.HTTP_200_OK: {"model": Page[ReleaseResponse]},
    },
)
@router.get(
    "/me" + s.API_RELEASE.prefix,
    tags=s.API_RELEASE.tags,
    responses={
        status.HTTP_200_OK: {"model": Page[ReleaseResponse]},
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
