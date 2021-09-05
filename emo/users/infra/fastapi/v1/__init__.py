from fastapi import APIRouter

from emo.settings import settings
from emo.users.infra.fastapi.v1 import token, users

users_router = APIRouter(
    responses={404: {"description": "Not found"}},
    **settings.API_V1.dict(),
)
users_router.include_router(users.router)
users_router.include_router(token.router)
