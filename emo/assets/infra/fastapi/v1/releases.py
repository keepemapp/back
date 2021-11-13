from typing import List, Type

import emo.assets.infra.fastapi.v1.schemas.releases as schemas
import emo.assets.infra.memrepo.views_asset_release as views
from emo.assets.domain.usecase import asset_in_a_bottle as b
from emo.assets.domain.usecase import asset_to_future_self as afs
from emo.assets.domain.usecase import stash as st
from emo.assets.domain.usecase import time_capsule as tc
from emo.assets.domain.usecase import transfer as tr
from emo.assets.domain.usecase.unit_of_work import AssetUoW
from emo.assets.infra.dependencies import message_bus, release_uow
from emo.settings import settings as s
from emo.shared.domain.usecase.message_bus import MessageBus
from emo.shared.infra.dependencies import get_active_user_token
from emo.shared.infra.fastapi.exceptions import UNAUTHORIZED_GENERIC
from emo.shared.infra.fastapi.schemas import HTTPError, TokenData
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse

router = APIRouter(
    responses={404: {"description": "Not found"}},
    **s.API_ASSET_PATH.dict(),
)


@router.get(
    "",
    responses={
        status.HTTP_200_OK: {"model": List[schemas.ReleaseResponse]},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
    },
)
async def get_all_transfers(
    token: TokenData = Depends(get_active_user_token),
    uow_cls: Type[AssetUoW] = Depends(release_uow),
):
    return [
        schemas.ReleaseResponse(**r)
        for r in views.get_releases(token.user_id, uow_cls())
    ]


@router.get(
    "/{release_id}",
    responses={
        status.HTTP_200_OK: {"model": List[schemas.ReleaseResponse]},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
        status.HTTP_404_NOT_FOUND: {"model": HTTPError},
    },
)
async def get_all_releases(
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
    "/to_future_self",
    status_code=status.HTTP_201_CREATED,
    response_description="Creates an asset to future self.\n"
    + "If successful, redirects to the GET ENDPOINT",
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": HTTPError},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": HTTPError},
    },
)
async def add_asset_future_self(
    create: schemas.CreateAssetToFutureSelf,
    token: TokenData = Depends(get_active_user_token),
    bus: MessageBus = Depends(message_bus),
):
    if token.user_id not in create.owner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str("Cannot create an asset you are not owner of"),
        )

    # TODO validate ownership here???

    payload = create.__dict__
    payload["owner"] = create.owner.replace("/users/", "")
    cmd = afs.CreateAssetToFutureSelf(**payload)
    bus.handle(cmd)
    return ""


@router.post(
    "/in_a_bottle",
    status_code=status.HTTP_201_CREATED,
    response_description="Creates an asset in a bottle.\n"
    + "If successful, redirects to the GET endpoint.",
    response_class=RedirectResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": HTTPError},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": HTTPError},
    },
)
async def add_asset_bottle(
    create: schemas.CreateAssetInABottle,
    token: TokenData = Depends(get_active_user_token),
    bus: MessageBus = Depends(message_bus),
):
    if token.user_id not in create.owner:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str("Cannot create an asset you are not owner of"),
        )

    # TODO validate ownership here???

    payload = create.__dict__
    payload["owner"] = [o.replace("/users/", "") for o in create.owner]
    cmd = b.CreateAssetInABottle(**payload)
    bus.handle(cmd)
    return RedirectResponse(
        url=s.
