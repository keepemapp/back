from fastapi import APIRouter

from emo.infrastructure.routers.endpoints import transfers, assets

api_router = APIRouter()
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(transfers.router, prefix="/transfers", tags=["transfers"])