from typing import List, Type

from fastapi import APIRouter, Depends, status

from kpm.assets.domain.usecase.unit_of_work import AssetUoW
from kpm.assets.infra.dependencies import unit_of_work_class
from kpm.assets.infra.fastapi.v1.assets import asset_to_response
from kpm.assets.infra.fastapi.v1.schemas import AssetResponse
from kpm.assets.infra.memrepo import views_asset
from kpm.settings import settings
from kpm.shared.infra.dependencies import get_active_user_token
from kpm.shared.infra.fastapi.schemas import HTTPError, TokenData

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
    uow_cls: Type[AssetUoW] = Depends(unit_of_work_class),
):
    assets = views_asset.find_by_ownerid(token.user_id, uow_cls())
    return [asset_to_response(a, token) for a in assets]
