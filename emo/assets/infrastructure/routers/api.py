from fastapi import APIRouter

from emo.assets.infrastructure.routers.endpoints import assets, transfers

api_router = APIRouter()
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(transfers.router, prefix="/transfers",
                          tags=["transfers"])
