from typing import List

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from emo.assets.domain.entity.asset import Asset
from emo.assets.infra.dependencies import asset_repository
from emo.assets.infra.fastapi.v1 import assets_router
from emo.assets.infra.fastapi.v1.schemas import AssetCreate, AssetResponse
from emo.settings import settings as s
from emo.shared.domain import UserId
from emo.shared.infra.dependencies import event_bus, get_active_user_token
from emo.shared.infra.fastapi.schema_utils import to_pydantic_model
from emo.shared.infra.fastapi.schemas import TokenData
from tests.assets.domain import valid_asset
from tests.assets.utils import MemoryAssetRepository
from tests.shared.utils import MemoryEventBus

ASSET_ROUTE: str = s.API_V1.concat(s.API_ASSET_PATH).prefix
ACTIVE_USER_TOKEN = TokenData(user_id="uid", disabled=False)


def active_user_token():
    return ACTIVE_USER_TOKEN


@pytest.fixture(scope="class")
def client() -> TestClient:
    app = FastAPI(
        title="MyHeritage User test",
    )
    app.include_router(assets_router)

    r = MemoryAssetRepository()
    e = MemoryEventBus()
    app.dependency_overrides[asset_repository] = lambda: r
    app.dependency_overrides[event_bus] = lambda: e
    app.dependency_overrides[get_active_user_token] = active_user_token
    yield TestClient(app)


def create_asset(client: TestClient, num: int, uids: List[str]):
    asset = AssetCreate(
        title=f"Asset number {num}",
        description=f"Description for {num}",
        owners_id=uids,
        type=f"Type of {num}",
        file_name=f"file_of_{num}.jpg",
    )
    response = client.post(ASSET_ROUTE, json=asset.dict())
    return asset, response


@pytest.mark.unit
class TestAssetResponseConversion:
    def test_asset_response(self, valid_asset):
        e = Asset(**valid_asset)
        p = to_pydantic_model(e, AssetResponse)


@pytest.mark.unit
class TestRegisterAsset:
    def test_create(self, client):
        uids = [ACTIVE_USER_TOKEN.user_id]
        asset = AssetCreate(
            title=f"Asset number",
            description=f"Description for",
            owners_id=uids,
            type=f"Type of ",
            file_name=f"file_of_.jpg",
        )
        response = client.post(ASSET_ROUTE, json=asset.dict())
        assert response.status_code == 200
        resp = response.json()
        assert resp.get("title") == asset.title
        assert resp.get("description") == asset.description
        for uid in uids:
            assert s.API_USER_PATH.prefix + "/" + uid in resp.get("owners_id")
        assert resp.get("type") == asset.type
        assert resp.get("file_name") == asset.file_name

    def test_create_multiple_owners(self, client):
        uids = [ACTIVE_USER_TOKEN.user_id, "other-owner"]
        asset = AssetCreate(
            title=f"Asset number",
            description=f"Description for",
            owners_id=uids,
            type=f"Type of ",
            file_name=f"file_of_.jpg",
        )
        response = client.post(ASSET_ROUTE, json=asset.dict())
        assert response.status_code == 200
        resp = response.json()
        for uid in uids:
            assert s.API_USER_PATH.prefix + "/" + uid in resp.get("owners_id")

    def test_cannot_create_if_not_owner(self, client):
        uids = ["another user id"]
        asset = AssetCreate(
            title=f"Asset number",
            description=f"Description for",
            owners_id=uids,
            type=f"Type of ",
            file_name=f"file_of_.jpg",
        )
        response = client.post(ASSET_ROUTE, json=asset.dict())
        assert response.status_code == 400


@pytest.mark.unit
class TestGetAssets:
    def test_user_assets(self, client: TestClient):
        _, r1 = create_asset(client, 0, [ACTIVE_USER_TOKEN.user_id])
        aid1 = r1.json().get("id")
        response = client.get(
            s.API_V1.concat(s.API_USER_PATH).prefix
            + "/me"
            + s.API_ASSET_PATH.prefix
        )
        assert response.status_code == 200
        json = response.json()
        assert len(json) == 1

        # Second asset
        _, r2 = create_asset(
            client, 0, ["other-user", ACTIVE_USER_TOKEN.user_id]
        )
        aid2 = r2.json().get("id")

        response = client.get(
            s.API_V1.concat(s.API_USER_PATH).prefix
            + "/me"
            + s.API_ASSET_PATH.prefix
        )
        assert response.status_code == 200
        json = response.json()
        assert len(json) == 2
        assert [a.get("id") for a in json] == [aid1, aid2]

    def test_get_individual_asset(self, client):
        _, r1 = create_asset(client, 0, [ACTIVE_USER_TOKEN.user_id])
        r1 = r1.json()
        r1["upload_path"] = None
        aid1 = r1.get("id")
        response = client.get(ASSET_ROUTE + "/" + aid1)
        assert response.status_code == 200
        assert response.json() == r1

    def test_non_existing_asset_gives_unauthorized(self, client):
        response = client.get(ASSET_ROUTE + "/random-asset-id")
        assert response.status_code == 401

    def test_get_multiple_owners_asset(self, client):
        owners = ["other_owner", ACTIVE_USER_TOKEN.user_id]
        _, r1 = create_asset(client, 0, owners)
        aid1 = r1.json().get("id")
        response = client.get(ASSET_ROUTE + "/" + aid1)
        assert response.status_code == 200
