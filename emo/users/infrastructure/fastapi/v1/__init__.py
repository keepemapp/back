from fastapi import APIRouter

from emo.settings import settings
from emo.users.infrastructure.fastapi.v1 import users, token

users_router = APIRouter(
    responses={404: {"description": "Not found"}},
    **settings.API_V1.dict(),
)
users_router.include_router(users.router)
users_router.include_router(token.router)
