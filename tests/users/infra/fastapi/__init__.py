import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from emo.shared.infra.dependencies import event_bus
from emo.users.infra.dependencies import user_repository
from emo.users.infra.fastapi.v1 import users_router
from tests.shared.utils import MemoryEventBus
from tests.users.utils import MemoryUserRepository


@pytest.fixture(scope="class")
def client() -> TestClient:
    app = FastAPI(
        title="MyHeritage User test",
    )
    app.include_router(users_router)

    r = MemoryUserRepository()
    e = MemoryEventBus()
    app.dependency_overrides[user_repository] = lambda: r
    app.dependency_overrides[event_bus] = lambda: e
    yield TestClient(app)
