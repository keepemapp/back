import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from kpm.shared.entrypoints.fastapi.dependencies import message_bus
from kpm.users.entrypoints.fastapi.v1 import users_router
from tests.users.fixtures import bus


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


__all__ = ["app", "client", "bus"]
