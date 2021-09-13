from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from emo.assets.domain.entity import AssetRepository
from emo.assets.domain.usecase.create_asset import CreateAsset
from emo.assets.infra.dependencies import asset_repository
from emo.assets.infra.fastapi.v1.schemas import AssetCreate, AssetResponse
from emo.settings import settings
from emo.shared.domain import AssetId, UserId
from emo.shared.domain.usecase import EventPublisher
from emo.shared.infra.dependencies import event_bus, get_active_user_token
from emo.shared.infra.fastapi.exceptions import UNAUTHORIZED_GENERIC
from emo.shared.infra.fastapi.schema_utils import to_pydantic_model
from emo.shared.infra.fastapi.schemas import HTTPError, TokenData

router = APIRouter(
    responses={404: {"description": "Not found"}},
    **settings.API_ASSET_PATH.dict(),
)


@router.post(
    "",
    responses={
        status.HTTP_200_OK: {"model": AssetResponse},
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
    return to_pydantic_model(uc.entity, AssetResponse)


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
    return [to_pydantic_model(u, AssetResponse) for u in repo.all()]


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
