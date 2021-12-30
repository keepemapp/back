from fastapi import APIRouter

from kpm.settings import settings
from kpm.users.entrypoints.fastapi.v1 import token
from kpm.users.entrypoints.fastapi.v1 import users

users_router = APIRouter(
    responses={404: {"description": "Not found"}},
    **settings.API_V1.dict(),
)
users_router.include_router(users.router)
users_router.include_router(token.router)
