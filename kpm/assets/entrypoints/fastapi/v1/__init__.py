from fastapi import APIRouter

from kpm.assets.entrypoints.fastapi.v1.assets import router
from kpm.assets.entrypoints.fastapi.v1.releases import router as r_router
from kpm.assets.entrypoints.fastapi.v1.users_resources import (
    router as u_router,
)
from kpm.settings import settings

assets_router = APIRouter(
    responses={404: {"description": "Not found"}},
    **settings.API_V1.dict(),
)
assets_router.include_router(router)
assets_router.include_router(u_router)
assets_router.include_router(r_router)
