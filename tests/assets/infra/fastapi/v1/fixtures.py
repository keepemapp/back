import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from kpm.shared.entrypoints.fastapi.dependencies import message_bus
from kpm.assets.entrypoints.fastapi.v1 import assets_router
from kpm.shared.entrypoints.auth_jwt import AccessToken
from kpm.shared.entrypoints.fastapi.jwt_dependencies import get_access_token
from tests.assets.utils import bus

ADMIN_TOKEN = AccessToken(subject="uid", scopes=["user", "admin"])
USER_TOKEN = AccessToken(subject="uid", scopes=["user"])



@pytest.fixture
def app(bus) -> FastAPI:
    app = FastAPI(
        title="User admin endpoint test",
    )
    app.include_router(assets_router)
    app.dependency_overrides[message_bus] = lambda: bus
    return app


@pytest.fixture
def admin_client(app) -> TestClient:
    app.dependency_overrides[get_access_token] = lambda: ADMIN_TOKEN
    yield TestClient(app)


@pytest.fixture
def user_client(app) -> TestClient:
    app.dependency_overrides[get_access_token] = lambda: USER_TOKEN
    yield TestClient(app)
