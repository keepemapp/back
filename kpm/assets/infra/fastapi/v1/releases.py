from typing import List, Type

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

import kpm.assets.infra.fastapi.v1.schemas.releases as schemas
import kpm.assets.infra.memrepo.views_asset_release as views
from kpm.assets.domain.entity.asset import Asset
from kpm.assets.domain.usecase import asset_in_a_bottle as b
from kpm.assets.domain.usecase import asset_to_future_self as afs
from kpm.assets.domain.usecase import stash as st
from kpm.assets.domain.usecase.unit_of_work import AssetUoW
from kpm.assets.infra.dependencies import message_bus, release_uow
from kpm.settings import settings as s
from kpm.shared.domain.usecase.message_bus import MessageBus
from kpm.shared.infra.dependencies import get_active_user_token
from kpm.shared.infra.fastapi.exceptions import UNAUTHORIZED_GENERIC
from kpm.shared.infra.fastapi.schemas import HTTPError, TokenData
import kpm.assets.infra.memrepo.views_asset as assets

router = APIRouter(
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str("You are not the owner"),
        )


def assert_assets_can_be_scheduled(bus, asset_list: List[str], owner: str):
    uow = bus.uows[Asset]
    as_clear = [a.replace('/assets/', '') for a in asset_list]
    o_clear = owner.replace('/users/', '')

    if not assets.are_assets_active(uow, as_clear, o_clear):
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Some assets do not exist or are not modifyable",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get(
    s.API_RELEASE.path(),
    responses={
        status.HTTP_200_OK: {"model": List[schemas.ReleaseResponse]},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
    },
)
async def get_releases(
    token: TokenData = Depends(get_active_user_token),
    uow_cls: Type[AssetUoW] = Depends(release_uow),
):
    return [
        schemas.ReleaseResponse(**r)
        for r in views.get_releases(token.user_id, uow_cls())
    ]


@router.get(
    s.API_RELEASE.path() + "/{release_id}",
    responses={
        status.HTTP_200_OK: {"model": List[schemas.ReleaseResponse]},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
        status.HTTP_404_NOT_FOUND: {"model": HTTPError},
    },
)
async def get_release(
    transfer_id: str,
    token: TokenData = Depends(get_active_user_token),
    uow_cls: Type[AssetUoW] = Depends(release_uow),
):
    release = views.get(transfer_id, uow_cls())
    if release and release.get("owner") == token.user_id:
        return schemas.ReleaseResponse(**release)
    else:
        raise UNAUTHORIZED_GENERIC


@router.post(
    s.API_FUTURE_SELF.path(),
    **BASE_API_POST_DEF,
    response_description="Creates an asset to future self.\n"
    + "If successful, redirects to the GET ENDPOINT",
)
async def add_asset_future_self(
    create: schemas.CreateAssetToFutureSelf,
    token: TokenData = Depends(get_active_user_token),
    bus: MessageBus = Depends(message_bus),
):
    error = assert_assets_can_be_scheduled(bus, create.assets, token.user_id)
    if error:
        raise error

    payload = create.__dict__
    cmd = afs.CreateAssetToFutureSelf(owner=token.user_id, **payload)
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
    token: TokenData = Depends(get_active_user_token),
    bus: MessageBus = Depends(message_bus),
):
    error = assert_assets_can_be_scheduled(bus, create.assets, token.user_id)
    if error:
        return error

    payload = create.__dict__
    cmd = b.CreateAssetInABottle(owner=token.user_id, **payload)
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
    token: TokenData = Depends(get_active_user_token),
    bus: MessageBus = Depends(message_bus),
):
    error = assert_assets_can_be_scheduled(bus, create.assets, token.user_id)
    if error:
        return error

    payload = create.__dict__
    cmd = st.Stash(owner=token.user_id, **payload)
    bus.handle(cmd)
    return post_response(cmd.aggregate_id)