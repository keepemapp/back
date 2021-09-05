from fastapi.testclient import TestClient

from emo.main import app
from emo.users.infra.dependencies import event_bus, user_repository
from tests.users.utils import MemoryEventBus, MemoryUserRepository


async def override_user_repo():
    return MemoryUserRepository()


async def override_event_bus():
    return MemoryEventBus()


def get_client() -> TestClient:
    app.dependency_overrides[user_repository] = override_user_repo
    app.dependency_overrides[event_bus] = override_event_bus
    return TestClient(app)
