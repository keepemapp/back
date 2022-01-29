from datetime import timedelta
from typing import Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.params import Query
from fastapi.responses import FileResponse, RedirectResponse
from fastapi_pagination import Page, Params, paginate
from jose import JWTError

import kpm.assets.domain.commands as cmds
import kpm.shared.entrypoints.fastapi.exceptions as ex
from kpm.assets.adapters.filestorage import AssetFileRepository
from kpm.assets.entrypoints.fastapi.dependencies import asset_file_repository
from kpm.assets.entrypoints.fastapi.v1.schemas import (
    AssetCreate,
    AssetResponse,
    AssetUpdatableFields,
    AssetUploadAuthData,
)
from kpm.settings import settings as s
from kpm.shared.domain.model import RootAggState
from kpm.shared.entrypoints.auth_jwt import AccessToken
from kpm.shared.entrypoints.fastapi import query_params
from kpm.shared.entrypoints.fastapi.dependencies import asset_view, message_bus
from kpm.shared.entrypoints.fastapi.jwt_dependencies import (
    create_jwt_token,
    decode_token,
    get_access_token,
    get_admin_token,
)
from kpm.shared.entrypoints.fastapi.schemas import HTTPError
from kpm.shared.log import logger
from kpm.shared.service_layer.message_bus import MessageBus

router = APIRouter(
    responses={404: {"description": "Not found"}},
    **s.API_ASSET_PATH.dict(),
)


def asset_to_response(asset_dict: Dict, token: AccessToken):
    resp = AssetResponse(**asset_dict)
    if asset_dict.get("state") == RootAggState.PENDING.value:
        resp.upload_path = create_asset_upload_path(resp.id, token.subject)
    return resp


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_description="If successful, redirects to the asset file upload"
    "path (POST) via the `location` header.",
    response_class=RedirectResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": HTTPError},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": HTTPError},
    },
)
async def add_asset(
    new_asset: AssetCreate,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
):
    if not new_asset.owners_id:
        new_asset.owners_id = [token.subject]
    if token.subject not in new_asset.owners_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str("Cannot create an asset you are not owner of"),
        )

    payload = new_asset.__dict__
    cmd = cmds.CreateAsset(**payload)
    bus.handle(cmd)
    return RedirectResponse(
        url=create_asset_upload_path(cmd.asset_id, token.subject),
        status_code=status.HTTP_201_CREATED,
    )


def create_asset_upload_auth_token(asset_id: str, user_id: str) -> str:
    auth = AssetUploadAuthData(asset_id=asset_id, user_id=user_id)
    return create_jwt_token(
        auth.dict(),
        expires_delta=timedelta(minutes=s.UPLOAD_AUTH_TOKEN_EXPIRE_SEC),
    )  # TODO change me to seconds instead of minutes


def create_asset_upload_path(asset_id: str, user_id: str) -> str:
    return (
        s.API_ASSET_PATH.concat(asset_id).prefix + "/file?authorizer_token="
        f"{create_asset_upload_auth_token(asset_id, user_id)}"
    )


def decode_asset_upload_token(token: str) -> AssetUploadAuthData:
    try:
        return decode_token(token, AssetUploadAuthData)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate authorizer token",
        )


add_asset_file_resp = {
    status.HTTP_201_CREATED: {},
    status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
    status.HTTP_403_FORBIDDEN: {"model": HTTPError},
    status.HTTP_400_BAD_REQUEST: {"model": HTTPError},
}


@router.put(
    "/{asset_id}/file",
    responses=add_asset_file_resp,
)
@router.post(
    "/{asset_id}/file", responses=add_asset_file_resp, deprecated=True
)
async def add_asset_file(
    asset_id: str,
    authorizer_token: str,
    token: AccessToken = Depends(get_access_token),
    file_repo: AssetFileRepository = Depends(asset_file_repository),
    bus: MessageBus = Depends(message_bus),
    views=Depends(asset_view),
    file: UploadFile = File(...),
):
    auth_data = decode_asset_upload_token(authorizer_token)
    a = views.find_by_id_and_owner(asset_id, token.subject, bus=bus)

    if not a:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Asset not found",
        )

    if auth_data.asset_id != asset_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mismatch in asset id and authorization",
        )
    if auth_data.user_id != token.subject:
        raise ex.FORBIDDEN_GENERIC

    if a["file_name"] != file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File names does not match",
        )
    # TODO when we go with encrypted files, content_type will be different
    if a["file_type"] != file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type does not match",
        )
    await file_repo.create(a["file_location"], file)
    bus.handle(cmds.UploadAssetFile(asset_id=asset_id))
    return RedirectResponse(
        url=router.url_path_for("get_asset_file", asset_id=asset_id),
        status_code=status.HTTP_201_CREATED,
    )


@router.get(
    "",
    responses={
        status.HTTP_200_OK: {"model": Page[AssetResponse]},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
        status.HTTP_403_FORBIDDEN: {"model": HTTPError},
    },
    tags=["admin"],
)
async def get_all_assets(
    order_by: str = query_params.order_by,
    order: str = query_params.order,
    file_types: str = Query(
        None,
        max_length=50,
        regex=r"^[^;\-'\"]+$",
        description="Comma separated list of file types.",
    ),
    bookmarked: bool = query_params.bookmarked,
    paginate_params: Params = Depends(),
    token: AccessToken = Depends(get_admin_token),
    views=Depends(asset_view),
    bus: MessageBus = Depends(message_bus),
):
    fts = []
    if file_types:
        fts = file_types.split(",")
    assets = views.all_assets(
        bus=bus,
        order_by=order_by,
        order=order,
        asset_types=fts,
        bookmarked=bookmarked,
    )
    return paginate(
        [asset_to_response(a, token) for a in assets], paginate_params
    )


@router.get(
    "/{asset_id}",
    responses={
        status.HTTP_200_OK: {"model": AssetResponse},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
        status.HTTP_403_FORBIDDEN: {"model": HTTPError},
    },
)
async def get_asset(
    asset_id: str,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
    views=Depends(asset_view),
):
    a = views.find_by_id_and_owner(asset_id, token.subject, bus=bus)
    if a:
        return asset_to_response(a, token)
    else:
        raise ex.FORBIDDEN_GENERIC


@router.patch(
    "/{asset_id}",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
        status.HTTP_403_FORBIDDEN: {"model": HTTPError},
    },
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_asset_fields(
    updates: AssetUpdatableFields,
    asset_id: str,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
    views=Depends(asset_view),
):
    """
    Idempotent update of asset fields
    """
    if views.owned_by(asset_id, token.subject, bus=bus):
        payload = updates.__dict__
        payload = {k: v for k, v in payload.items() if v is not None}
        if "tags" in payload.keys():
            payload["tags"] = set(payload.get("tags") or [])
        if "people" in payload.keys():
            payload["people"] = set(payload.get("people") or [])
        payload["asset_id"] = asset_id
        cmd = cmds.UpdateAssetFields(**payload)

        bus.handle(cmd)
    else:
        raise ex.FORBIDDEN_GENERIC


@router.delete(
    "/{asset_id}",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
        status.HTTP_403_FORBIDDEN: {"model": HTTPError},
    },
    status_code=status.HTTP_200_OK,
)
async def remove_asset_fields(
    asset_id: str,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
    file_repo: AssetFileRepository = Depends(asset_file_repository),
    views=Depends(asset_view),
):
    """
    Removes an asset and its file
    """
    a = views.find_by_id_and_owner(asset_id, token.subject, bus=bus)
    if a:
        cmd = cmds.RemoveAsset(asset_id=asset_id)
        bus.handle(cmd)
        try:
            file_repo.delete(a["file_location"])
        except Exception:
            logger.error(f"File {a['file_location']} could not be deleted.")
    else:
        raise ex.FORBIDDEN_GENERIC


@router.get(
    "/{asset_id}/file",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
        status.HTTP_403_FORBIDDEN: {"model": HTTPError},
    },
)
async def get_asset_file(
    asset_id: str,
    token: AccessToken = Depends(get_access_token),
    bus: MessageBus = Depends(message_bus),
    file_repo: AssetFileRepository = Depends(asset_file_repository),
    views=Depends(asset_view),
):
    """Returns the asset's binary file"""
    a = views.find_by_id_and_owner(asset_id, token.subject, bus=bus)
    if a:
        # TODO when we go with encrypted files, media_type will be different
        try:
            return FileResponse(
                file_repo.get(a["file_location"]), media_type=a["file_type"]
            )
        except RuntimeError as e:
            raise HTTPException(detail=e.msg)
    else:
        raise ex.FORBIDDEN_GENERIC
