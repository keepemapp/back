import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from kpm.shared.entrypoints.auth_jwt import AccessToken
from kpm.shared.entrypoints.fastapi.dependencies import message_bus
from kpm.shared.entrypoints.fastapi.jwt_dependencies import get_access_token
from kpm.users.entrypoints.fastapi.v1 import users_router
from tests.users.fixtures import bus


ADMIN_TOKEN = AccessToken(subject="admin", scopes=["user", "admin"])
USER_TOKEN = AccessToken(subject="user", scopes=["user"])
ATTACKER_TOKEN = AccessToken(subject="attacker", scopes=["user", "admin"])


@pytest.fixture
def app(bus) -> FastAPI:
    app = FastAPI(
        title="User test",
    )
    app.include_router(users_router)
    app.dependency_overrides[message_bus] = lambda: bus
    return app


@pytest.fixture
def client(app) -> TestClient:
    yield TestClient(app)


@pytest.fixture
def admin_client(bus) -> TestClient:
    app = FastAPI(title="Admin client")
    app.include_router(users_router)
    app.dependency_overrides[message_bus] = lambda: bus
    app.dependency_overrides[get_access_token] = lambda: ADMIN_TOKEN
    yield TestClient(app)


@pytest.fixture
def user_client(bus) -> TestClient:
    app = FastAPI(title="User client")
    app.include_router(users_router)
    app.dependency_overrides[message_bus] = lambda: bus
    app.dependency_overrides[get_access_token] = lambda: USER_TOKEN
    yield TestClient(app)


@pytest.fixture
def attacker_client(bus) -> TestClient:
    app = FastAPI(title="Attacker client")
    app.include_router(users_router)
    app.dependency_overrides[message_bus] = lambda: bus
    app.dependency_overrides[get_access_token] = lambda: ATTACKER_TOKEN
    yield TestClient(app)


__all__ = ["app", "client", "bus", "admin_client", "user_client",
           "attacker_client", "ADMIN_TOKEN", "USER_TOKEN", "ATTACKER_TOKEN"]
