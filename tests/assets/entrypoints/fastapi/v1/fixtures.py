import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from kpm.assets.entrypoints.fastapi.v1 import assets_router
from kpm.shared.entrypoints.auth_jwt import AccessToken
from kpm.shared.entrypoints.fastapi.dependencies import message_bus
from kpm.shared.entrypoints.fastapi.jwt_dependencies import get_access_token
from tests.assets.utils import bus

ADMIN_TOKEN = AccessToken(subject="adminid", scopes=["user", "admin"])
USER_TOKEN = AccessToken(subject="uid", scopes=["user"])
USER2_TOKEN = AccessToken(subject="uid2", scopes=["user"])
ATTACKER_TOKEN = AccessToken(subject="attacker", scopes=["user", "admin"])


@pytest.fixture
def app(bus) -> FastAPI:
    app = FastAPI(
        title="User admin endpoint test",
    )
    app.include_router(assets_router)
    app.dependency_overrides[message_bus] = lambda: bus
    return app


@pytest.fixture
def admin_client(bus) -> TestClient:
    app = FastAPI(title="Admin client")
    app.include_router(assets_router)
    app.dependency_overrides[message_bus] = lambda: bus
    app.dependency_overrides[get_access_token] = lambda: ADMIN_TOKEN
    yield TestClient(app)


@pytest.fixture
def user_client(bus) -> TestClient:
    app = FastAPI(title="User client")
    app.include_router(assets_router)
    app.dependency_overrides[message_bus] = lambda: bus
    app.dependency_overrides[get_access_token] = lambda: USER_TOKEN
    yield TestClient(app)
