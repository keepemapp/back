import pytest
from fastapi.testclient import TestClient

from emo.main import app
from emo.users.infra.dependencies import event_bus, user_repository
from tests.shared.utils import MemoryEventBus
from tests.users.utils import MemoryUserRepository


@pytest.fixture(scope="session")
def client() -> TestClient:
    r = MemoryUserRepository()
    e = MemoryEventBus()
    app.dependency_overrides[user_repository] = lambda: r
    app.dependency_overrides[event_bus] = lambda: e
    yield TestClient(app)
