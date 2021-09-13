from fastapi import APIRouter

from emo.assets.infra.fastapi.v1.assets import router
from emo.assets.infra.fastapi.v1.users_resources import router as u_router
from emo.settings import settings

assets_router = APIRouter(
    responses={404: {"description": "Not found"}},
    **settings.API_V1.dict(),
)
assets_router.include_router(router)
assets_router.include_router(u_router)
