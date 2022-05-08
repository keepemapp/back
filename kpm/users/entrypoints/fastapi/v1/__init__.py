from fastapi import APIRouter

from kpm.settings import settings
from kpm.users.entrypoints.fastapi.v1 import cross_domain_endpoints, feedback, \
    keeps, token, users

users_router = APIRouter(
    responses={404: {"description": "Not found"}},
    **settings.API_V1.dict(),
)
users_router.include_router(users.router)
users_router.include_router(token.router)
users_router.include_router(keeps.router)
users_router.include_router(feedback.router)
users_router.include_router(cross_domain_endpoints.router)
