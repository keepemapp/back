from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi_pagination import Page, Params, paginate

import kpm.assets.domain.commands as cmds
import kpm.assets.entrypoints.fastapi.v1.schemas.releases as schemas
import kpm.shared.entrypoints.fastapi.exceptions as ex
from kpm.settings import settings as s
from kpm.shared.entrypoints.auth_jwt import AccessToken
from kpm.shared.entrypoints.fastapi.dependencies import asset_rel_view, \
    asset_view, message_bus
from kpm.shared.entrypoints.fastapi.jwt_dependencies import (
    get_access_token,
    get_admin_token,
)
from kpm.shared.entrypoints.fastapi.schemas import HTTPError
from kpm.shared.service_layer.message_bus import MessageBus

router = APIRouter(
    tags=s.API_RELEASE.tags,
    responses={404: {"description": "Not found"}},
)

BASE_API_POST_DEF = {
    "status_code": status.HTTP_201_CREATED,
    "response_class": RedirectResponse,
    "responses": {
        status.HTTP_400_BAD_REQUEST: {"model": HTTPError},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": HTTPError},
    },
}


def post_response(*args) -> RedirectResponse:
    uri = s.API_RELEASE
    for r in args:
        uri = uri.concat(r)
    return RedirectResponse(
        url=uri,
        status_code=status.HTTP_201_CREATED,
    )


def assert_same_user(a, b):
    if a not in b:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str("You are not the owner"),
        )


def assert_assets_can_be_scheduled(bus, asset_list: List[str], owner: str, asset_view):
    as_clear = [a.replace("/assets/", "") for a in asset_list]
    o_clear = owner.replace("/users/", "")

    if not asset_view.are_assets_active(as_clear, bus=bus, user=o_clear):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Some assets do not exist or are not modifyable",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get(
    s.API_RELEASE.path(),
    responses={
        status.HTTP_200_OK: {"model": Page[schemas.ReleaseResponse]},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
        status.HTTP_403_FORBIDDEN: {"model": HTTPError},
    },
    tags=["admin"],
)
async def get_releases(
    params: Params = Depends(),
    token: AccessToken = Depends(get_admin_token),
    bus: MessageBus = Depends(message_bus),
    views=Depends(asset_rel_view),
):
    return paginate(
        [schemas.ReleaseResponse(**r) for r in views.all(bus=bus)], params
    )


@router.get(
    s.API_RELEASE.path() + "/{release_id}",
    responses={
        status.HTTP_200_OK: {"model": schemas.ReleaseResponse},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
        status.HTTP_403_FORBIDDEN: {"model": HTTPError},
        status.HTTP_404_NOT_FOUND: {"model": HTTPError},
    },
)
async def get_release(
    release_id: str,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
    views=Depends(asset_rel_view),
):
    release = views.get(release_id, bus=bus)
    if release and release.get("owner") == token.subject:
        return schemas.ReleaseResponse(**release)
    else:
        raise ex.FORBIDDEN_GENERIC


@router.post(
    s.API_FUTURE_SELF.path(),
    **BASE_API_POST_DEF,
    response_description="Creates an asset to future self.\n"
    + "If successful, redirects to the GET ENDPOINT",
)
async def add_asset_future_self(
    create: schemas.CreateAssetToFutureSelf,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
    assets=Depends(asset_view),
):
    error = assert_assets_can_be_scheduled(bus, create.assets, token.subject, assets)
    if error:
        raise error

    payload = {k: v for k, v in create.__dict__.items() if v}
    cmd = cmds.CreateAssetToFutureSelf(owner=token.subject, **payload)
    bus.handle(cmd)
    return post_response(cmd.aggregate_id)


@router.post(
    s.API_ASSET_BOTTLE.path(),
    **BASE_API_POST_DEF,
    response_description="Creates an asset in a bottle.\n"
    + "If successful, redirects to the GET endpoint.",
)
async def add_asset_bottle(
    create: schemas.CreateAssetInABottle,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
    assets=Depends(asset_view),
):
    error = assert_assets_can_be_scheduled(bus, create.assets, token.subject, assets)
    if error:
        raise error

    payload = {k: v for k, v in create.__dict__.items() if v}
    cmd = cmds.CreateAssetInABottle(owner=token.subject, **payload)
    bus.handle(cmd)
    return post_response(cmd.aggregate_id)


@router.post(
    s.API_STASH.path(),
    **BASE_API_POST_DEF,
    response_description="Stashes a group of assets.\n"
    + "If successful, redirects to the GET endpoint.",
)
async def add_stash(
    create: schemas.CreateAssetInABottle,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
    assets=Depends(asset_view),
):
    error = assert_assets_can_be_scheduled(bus, create.assets, token.subject, assets)
    if error:
        raise error

    payload = {k: v for k, v in create.__dict__.items() if v}
    cmd = cmds.Stash(owner=token.subject, **payload)
    bus.handle(cmd)
    return post_response(cmd.aggregate_id)
