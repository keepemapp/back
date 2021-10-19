from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from jose import JWTError

from emo.assets.domain.entity import Asset, AssetRepository
from emo.assets.domain.usecase.create_asset import CreateAsset
from emo.assets.infra.dependencies import (
    asset_file_repository,
    asset_repository,
)
from emo.assets.infra.fastapi.v1.schemas import (
    AssetCreate,
    AssetResponse,
    AssetUploadAuthData,
)
from emo.assets.infra.filestorage import AssetFileRepository
from emo.settings import settings
from emo.shared.domain import AssetId, UserId
from emo.shared.domain.usecase import EventPublisher
from emo.shared.infra.dependencies import (
    create_jwt_token,
    decode_token,
    event_bus,
    get_active_user_token,
)
from emo.shared.infra.fastapi.exceptions import UNAUTHORIZED_GENERIC
from emo.shared.infra.fastapi.schema_utils import to_pydantic_model
from emo.shared.infra.fastapi.schemas import HTTPError, TokenData

router = APIRouter(
    responses={404: {"description": "Not found"}},
    **settings.API_ASSET_PATH.dict(),
)


def asset_to_response(a: Asset, token: TokenData):
    resp = to_pydantic_model(a, AssetResponse)
    # TODO provide upload path only if no file was uploaded before
    resp.upload_path = create_asset_upload_path(a, token.user_id)
    return resp


@router.post(
    "",
    responses={
        status.HTTP_201_CREATED: {"model": AssetResponse},
        status.HTTP_400_BAD_REQUEST: {"model": HTTPError},
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": HTTPError},
    },
)
async def add_asset(
    new_asset: AssetCreate,
    token: TokenData = Depends(get_active_user_token),
    repo: AssetRepository = Depends(asset_repository),
    bus: EventPublisher = Depends(event_bus),
):
    if token.user_id not in new_asset.owners_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str("Cannot create an asset you are not owner of"),
        )

    payload = new_asset.__dict__
    owners = [UserId(o) for o in new_asset.owners_id]
    del payload["owners_id"]
    uc = CreateAsset(
        repository=repo,
        message_bus=bus,
        **payload,
        owners_id=owners,
    )
    try:
        uc.execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    # TODO provide pre-signed url
    return asset_to_response(uc.entity, token)


def create_asset_upload_auth_token(a: Asset, uid: str) -> str:
    auth = AssetUploadAuthData(asset_id=a.id.id, user_id=uid)
    return create_jwt_token(
        auth.dict(),
        expires_delta=timedelta(minutes=settings.UPLOAD_AUTH_TOKEN_EXPIRE_SEC),
    )  # TODO change me to seconds instead of minutes


def create_asset_upload_path(a: Asset, uid: str) -> str:
    return (
        settings.API_ASSET_PATH.concat(a.id.id).prefix
        + f"?authorizer_token={create_asset_upload_auth_token(a, uid)}"
    )


def decode_asset_upload_token(token: str) -> AssetUploadAuthData:
    try:
        return decode_token(token, AssetUploadAuthData)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate authorizer token",
        )


@router.post(
    "/{asset_id}",
    responses={
        status.HTTP_201_CREATED: {},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
        status.HTTP_400_BAD_REQUEST: {"model": HTTPError},
    },
)
async def post_asset_file(
    asset_id: str,
    authorizer_token: str,
    token: TokenData = Depends(get_active_user_token),
    file_repo: AssetFileRepository = Depends(asset_file_repository),
    repo: AssetRepository = Depends(asset_repository),
    file: UploadFile = File(...),
):
    auth_data = decode_asset_upload_token(authorizer_token)

    a = repo.find_by_id_and_ownerid(AssetId(asset_id), UserId(token.user_id))

    if not a:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Asset not found",
        )

    if auth_data.asset_id != asset_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mismatch in asset id and authorization",
        )
    if auth_data.user_id != token.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You do not own this authorization",
        )

    if a.file_name != file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File names does not match",
        )
    # TODO when we go with encrypted files, content_type will be different
    if a.type != file.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File type does not match",
        )
    await file_repo.create(a.file_location, file)
    return {}  # TODO return URL to get the image??


@router.get(
    "",
    responses={
        status.HTTP_200_OK: {"model": List[AssetResponse]},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
    },
)
async def get_all_assets(
    token: TokenData = Depends(get_active_user_token),
    repo: AssetRepository = Depends(asset_repository),
):
    # TODO change me. Allow only admins
    res = []
    for u in repo.all():
        resp = to_pydantic_model(u, AssetResponse)
        resp.upload_path = create_asset_upload_path(u, token.user_id)
        res.append(resp)
    return res


@router.get(
    "/{asset_id}",
    responses={
        status.HTTP_200_OK: {"model": AssetResponse},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
    },
)
async def get_asset(
    asset_id: str,
    token: TokenData = Depends(get_active_user_token),
    repo: AssetRepository = Depends(asset_repository),
):
    a = repo.find_by_id_and_ownerid(AssetId(asset_id), UserId(token.user_id))

    if a:
        return to_pydantic_model(a, AssetResponse)
    else:
        raise UNAUTHORIZED_GENERIC


@router.get(
    "/{asset_id}/file",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
    },
)
async def get_asset_file(
    asset_id: str,
    token: TokenData = Depends(get_active_user_token),
    repo: AssetRepository = Depends(asset_repository),
    file_repo: AssetFileRepository = Depends(asset_file_repository),
):
    """Returns the asset's binary file"""
    a = repo.find_by_id_and_ownerid(AssetId(asset_id), UserId(token.user_id))

    if a:
        # TODO when we go with encrypted files, media_type will be different
        return FileResponse(file_repo.get(a.file_location), media_type=a.type)
    else:
        raise UNAUTHORIZED_GENERIC
