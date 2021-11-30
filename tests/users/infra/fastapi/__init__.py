import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from kpm.users.infra.dependencies import user_repository
from kpm.users.infra.fastapi.v1 import users_router
from tests.users.utils import MemoryUserRepository


@pytest.fixture
def client() -> TestClient:
    app = FastAPI(
        title="MyHeritage User test",
    )
    app.include_router(users_router)

    r = MemoryUserRepository()
    app.dependency_overrides[user_repository] = lambda: r
    yield TestClient(app)
