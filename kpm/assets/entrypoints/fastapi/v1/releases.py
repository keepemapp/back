from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi_pagination import Page, Params, paginate

import kpm.assets.domain.commands as cmds
import kpm.assets.entrypoints.fastapi.v1.schemas.releases as schemas
import kpm.shared.entrypoints.fastapi.exceptions as ex
from kpm.assets.domain import OperationTriggerException
from kpm.settings import settings as s
from kpm.shared.domain.model import UserNotAllowedException
from kpm.shared.entrypoints.auth_jwt import AccessToken
from kpm.shared.entrypoints.fastapi.dependencies import (
    asset_rel_view,
    asset_view,
    message_bus,
)
from kpm.shared.entrypoints.fastapi.jwt_dependencies import (
    get_access_token,
    get_admin_token,
)
from kpm.shared.entrypoints.fastapi.schemas import HTTPError
from kpm.shared.service_layer.message_bus import MessageBus

router = APIRouter(
    tags=s.API_LEGACY.tags,
    responses={404: {"description": "Not found"}},
)

BASE_API_POST_DEF = {
    "status_code": status.HTTP_201_CREATED,
    "response_class": RedirectResponse,
    "responses": {
        status.HTTP_400_BAD_REQUEST: {"model": HTTPError},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": HTTPError},
    },
    "response_description": "If successful, redirects to the GET ENDPOINT",
}


def post_response(*args) -> RedirectResponse:
    uri = s.API_LEGACY
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


def assert_assets_can_be_scheduled(
    bus, asset_list: List[str], owner: str, asset_view
):
    as_clear = [a.replace("/assets/", "") for a in asset_list]
    o_clear = owner.replace("/users/", "")

    if not asset_view.are_assets_active(as_clear, bus=bus, user=o_clear):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Some assets do not exist or are not modifyable",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get(
    s.API_LEGACY.path(),
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


@router.post(
    s.API_LEGACY.concat(s.API_FUTURE_SELF).path(),
    **BASE_API_POST_DEF,
    description="Creates an asset to future self.",
)
async def create_asset_to_future_self(
    create: schemas.CreateAssetToFutureSelf,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
    assets=Depends(asset_view),
):
    error = assert_assets_can_be_scheduled(
        bus, create.assets, token.subject, assets
    )
    if error:
        raise error

    payload = {
        k: v for k, v in create.__dict__.items() if v
    }  # Clean None vals
    cmd = cmds.CreateAssetToFutureSelf(owner=token.subject, **payload)
    bus.handle(cmd)
    return post_response(cmd.aggregate_id)


@router.post(
    s.API_LEGACY.concat(s.API_ASSET_BOTTLE).path(),
    **BASE_API_POST_DEF,
    description="Creates an asset in a bottle.",
)
async def create_asset_in_a_bottle(
    create: schemas.CreateAssetInABottle,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
    assets=Depends(asset_view),
):
    error = assert_assets_can_be_scheduled(
        bus, create.assets, token.subject, assets
    )
    if error:
        raise error

    payload = {
        k: v for k, v in create.__dict__.items() if v
    }  # Clean None vals
    cmd = cmds.CreateAssetInABottle(owner=token.subject, **payload)
    bus.handle(cmd)
    return post_response(cmd.aggregate_id)


@router.post(
    s.API_LEGACY.concat(s.API_HIDE).path(),
    **BASE_API_POST_DEF,
    description="Hides a group of assets as legacy operation.",
)
async def create_hide_and_seek(
    create: schemas.CreateHideAndSeek,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
    assets=Depends(asset_view),
):
    error = assert_assets_can_be_scheduled(
        bus, create.assets, token.subject, assets
    )
    if error:
        raise error

    payload = {
        k: v for k, v in create.__dict__.items() if v
    }  # Clean None vals
    cmd = cmds.CreateHideAndSeek(owner=token.subject, **payload)
    bus.handle(cmd)
    return post_response(cmd.aggregate_id)


@router.post(
    s.API_LEGACY.concat(s.API_TRANSFER).path(),
    **BASE_API_POST_DEF,
    description="Schedules an asset transfer.",
)
async def create_transfer(
    create: schemas.CreateTransfer,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
    assets=Depends(asset_view),
):
    error = assert_assets_can_be_scheduled(
        bus, create.assets, token.subject, assets
    )
    if error:
        raise error

    payload = {
        k: v for k, v in create.__dict__.items() if v
    }  # Clean None vals
    cmd = cmds.CreateTransfer(owner=token.subject, **payload)
    bus.handle(cmd)
    return post_response(cmd.aggregate_id)


@router.post(
    s.API_LEGACY.concat(s.API_TIME_CAPSULE).path(),
    **BASE_API_POST_DEF,
    description="Creates a time capsule as a legacy operation.",
)
async def create_time_capsule(
    create: schemas.CreateTimeCapsule,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
    assets=Depends(asset_view),
):
    error = assert_assets_can_be_scheduled(
        bus, create.assets, token.subject, assets
    )
    if error:
        raise error

    payload = {
        k: v for k, v in create.__dict__.items() if v
    }  # Clean None vals
    cmd = cmds.CreateTimeCapsule(owner=token.subject, **payload)
    bus.handle(cmd)
    return post_response(cmd.aggregate_id)


@router.get(
    s.API_LEGACY.path() + "/{operation_id}",
    responses={
        status.HTTP_200_OK: {"model": schemas.ReleaseResponse},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
        status.HTTP_403_FORBIDDEN: {"model": HTTPError},
        status.HTTP_404_NOT_FOUND: {"model": HTTPError},
    },
)
async def get_release(
    operation_id: str,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
    views=Depends(asset_rel_view),
):
    release = views.get(operation_id, bus=bus)
    if release and release.get("owner") == token.subject:
        return schemas.ReleaseResponse(**release)
    else:
        raise ex.FORBIDDEN_GENERIC


@router.post(
    s.API_LEGACY.concat("{operation_id}", "trigger").path(),
    response_description="204 if successful, 403 if could not be triggered.",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": HTTPError},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": HTTPError},
        status.HTTP_403_FORBIDDEN: {
            "description": "Returned if trigger is not ready to execute or"
            " the user cannot trigger it."
        },
    },
)
async def trigger_legacy_operation(
    operation_id: str,
    create: schemas.ReleaseTrigger,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
):
    """
    Tries to trigger a legacy operation.

    To be successful, the following conditions must be met:

    * The user executing this request is a receiver of the legacy op
    * Current server time (UTC) is after the specified schedule_date (UTC)
    * Matches the geographical location passed (lowecased string comparison)
    """
    payload = {k: v for k, v in create.__dict__.items() if v}
    cmd = cmds.TriggerRelease(
        by_user=token.subject, aggregate_id=operation_id, **payload
    )
    try:
        bus.handle(cmd)
    except UserNotAllowedException:
        raise ex.FORBIDDEN_GENERIC
    except OperationTriggerException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot be triggered yet.",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.delete(
    s.API_LEGACY.concat("{operation_id}").path(),
    response_description="204 if successful, 403 if could not be triggered.",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def cancel_operation(
    operation_id: str,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
):
    """
    Used to decline/cancel a legacy operation
    """
    cmd = cmds.CancelRelease(by_user=token.subject, aggregate_id=operation_id)
    try:
        bus.handle(cmd)
    except UserNotAllowedException:
        raise ex.FORBIDDEN_GENERIC
    except OperationTriggerException:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot be triggered yet.",
            headers={"WWW-Authenticate": "Bearer"},
        )
