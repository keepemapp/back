from fastapi import APIRouter

from emo.users.infrastructure.fastapi.v1 import users, token

users_router = APIRouter()
users_router.include_router(users.router)
users_router.include_router(token.router)
