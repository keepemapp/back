from typing import List

from fastapi import APIRouter, Depends, status

from emo.assets.domain.entity import AssetRepository
from emo.assets.infra.dependencies import asset_repository
from emo.assets.infra.fastapi.v1.schemas import AssetResponse
from emo.settings import settings
from emo.shared.domain import UserId
from emo.shared.infra.dependencies import get_active_user_token
from emo.shared.infra.fastapi.schema_utils import to_pydantic_model
from emo.shared.infra.fastapi.schemas import HTTPError, TokenData

router = APIRouter(
    responses={404: {"description": "Not found"}},
    prefix=settings.API_USER_PATH.prefix,
)


@router.get(
    "/me" + settings.API_ASSET_PATH.prefix,
    tags=settings.API_ASSET_PATH.tags,
    responses={
        status.HTTP_200_OK: {"model": List[AssetResponse]},
        status.HTTP_401_UNAUTHORIZED: {"model": HTTPError},
    },
)
async def get_user_assets(
    token: TokenData = Depends(get_active_user_token),
    repo: AssetRepository = Depends(asset_repository),
):
    assets = repo.find_by_ownerid(UserId(token.user_id))
    return [to_pydantic_model(u, AssetResponse) for u in assets]
