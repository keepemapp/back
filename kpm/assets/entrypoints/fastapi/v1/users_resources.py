from fastapi import APIRouter, Depends, status
from fastapi.params import Query
from fastapi_pagination import Page, Params, paginate

import kpm.assets.adapters.memrepo.views_asset_release as views_releases
from kpm.assets.adapters.memrepo import views_asset
from kpm.assets.entrypoints.fastapi.v1.assets import asset_to_response
from kpm.assets.entrypoints.fastapi.v1.schemas import (AssetResponse,
                                                       ReleaseResponse)
from kpm.settings import settings as s
from kpm.shared.entrypoints.auth_jwt import AccessToken
from kpm.shared.entrypoints.fastapi.dependencies import message_bus
from kpm.shared.entrypoints.fastapi.jwt_dependencies import get_access_token
from kpm.shared.entrypoints.fastapi.schemas import HTTPError
from kpm.shared.service_layer.message_bus import MessageBus

router = APIRouter(
    responses={
        404: {"description": "Not found"},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
    },
)


@router.get(
    s.API_USER_PATH.concat("me", s.API_ASSET_PATH).path(),
    deprecated=True,
    tags=s.API_ASSET_PATH.tags,
    responses={status.HTTP_200_OK: {"model": Page[AssetResponse]}},
)
@router.get(
    "/me" + s.API_ASSET_PATH.prefix,
    tags=s.API_ASSET_PATH.tags,
    responses={status.HTTP_200_OK: {"model": Page[AssetResponse]}},
)
async def get_current_user_assets(
    order_by: str = Query(
        None,
        max_length=20,
        regex=r"^[^;\-'\"]+$",
        description="Attribute to sort by",
    ),
    order: str = Query(
        "asc",
        max_length=4,
        regex=r"^[^;\-'\"]+$",
        description="Available options: 'asc', 'desc'",
    ),
    file_types: str = Query(
        None,
        max_length=50,
        regex=r"^[^;\-'\"]+$",
        description="Comma separated list of file types.",
    ),
    paginate_params: Params = Depends(),
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
):
    fts = []
    if file_types:
        fts = file_types.split(",")
    assets = views_asset.find_by_ownerid(
        token.subject, bus=bus, order_by=order_by, order=order, asset_types=fts
    )
    return paginate(
        [asset_to_response(a, token) for a in assets], paginate_params
    )


@router.get(
    "/me" + s.API_ASSET_PATH.concat("stats").path(),
    tags=s.API_ASSET_PATH.tags,
)
async def get_asset_statistics(
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
):
    """Returns statistics regarding user assets."""
    stats = views_asset.user_stats(token.subject, bus=bus)
    return stats


@router.get(
    "/me" + s.API_ASSET_PATH.concat("of-the-week").path(),
    tags=s.API_ASSET_PATH.tags,
)
async def get_assets_of_the_week(
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
):
    """Returns the user's assets of the week.

    Currently every time you call the endpoint returns different assets.
    So it's on the client to cache hem for a period of time.
    TODO: Not return random assets.
    TODO: cache that decision for device compatibility
    """
    return views_asset.assets_of_the_week(token.subject, bus=bus)


@router.get(
    s.API_USER_PATH.concat("me", s.API_RELEASE).path(),
    deprecated=True,
    tags=s.API_RELEASE.tags,
    responses={status.HTTP_200_OK: {"model": Page[ReleaseResponse]}},
)
@router.get(
    "/me" + s.API_RELEASE.prefix,
    tags=s.API_RELEASE.tags,
    responses={status.HTTP_200_OK: {"model": Page[ReleaseResponse]}},
)
async def get_current_user_releases(
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


@router.get(
    "/me" + s.API_RELEASE.concat("stats").path(),
    tags=s.API_RELEASE.tags,
)
async def get_releases_statistics(
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
):
    """Returns statistics regarding releases assets."""
    stats = views_releases.user_stats(token.subject, bus=bus)
    return stats
