import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from kpm.assets.entrypoints.fastapi.dependencies import message_bus
from kpm.shared.entrypoints.auth_jwt import AccessToken
from kpm.shared.entrypoints.fastapi.jwt_dependencies import get_access_token
from kpm.users.infra.dependencies import user_repository
from kpm.users.infra.fastapi.v1 import users_router
from tests.assets.utils import bus
from tests.users.utils import MemoryUserRepository

ADMIN_TOKEN = AccessToken(subject="uid", scopes=["user", "admin"])
USER_TOKEN = AccessToken(subject="uid", scopes=["user"])


@pytest.fixture
def app(bus) -> FastAPI:
    app = FastAPI(
        title="User admin endpoint test",
    )
    app.include_router(users_router)

    r = MemoryUserRepository()
    app.dependency_overrides[user_repository] = lambda: r
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


@pytest.mark.unit
class TestAdminEndpoints:
    def test_user_denied(self, app, user_client):
        api_rs = [r for r in app.routes if isinstance(r, APIRoute)]
        admin_routes = [r for r in api_rs if "admin" in r.tags]
        for r in admin_routes:
            for method in r.methods:
                resp = user_client.request(method, r.path)
                assert resp.status_code == 403

    def test_admin_allowed(self, app, admin_client):
        api_rs = [r for r in app.routes if isinstance(r, APIRoute)]
        admin_routes = [r for r in api_rs if "admin" in r.tags]
        for r in admin_routes:
            for method in r.methods:
                resp = admin_client.request(method, r.path)
                assert resp.status_code != 403
