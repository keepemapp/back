import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from kpm.settings import settings as s
from kpm.shared.infra.fastapi.v1.common_endpoints import router


@pytest.fixture
def client() -> TestClient:
    app = FastAPI(
        title="Common test",
        prefix=s.API_V1.prefix,
    )
    app.include_router(router)

    yield TestClient(app)


@pytest.mark.unit
class TestCommonEndpoints:
    def test_health(self, client):
        response = client.get(s.API_V1.concat(s.API_HEALTH).prefix)
        assert response.status_code == 200
        assert "OK" in response.text

    def test_version(self, client):
        response = client.get(s.API_V1.concat(s.API_VERSION).prefix)
        assert response.status_code == 200
        assert list(response.json().keys()) == ["branch", "version"]
