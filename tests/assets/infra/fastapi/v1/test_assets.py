from typing import List

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from emo.assets.domain.entity.asset import Asset
from emo.assets.infra.bootstrap import bootstrap
from emo.assets.infra.dependencies import (asset_repository, message_bus,
                                           unit_of_work_class)
from emo.assets.infra.fastapi.v1 import assets_router
from emo.assets.infra.fastapi.v1.schemas import AssetCreate, AssetResponse
from emo.settings import settings as s
from emo.shared.domain import UserId
from emo.shared.infra.dependencies import event_bus, get_active_user_token
from emo.shared.infra.fastapi.schemas import TokenData
from tests.assets.domain import valid_asset
from tests.assets.utils import FakeAssetUoW, MemoryAssetRepository
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
    uow = FakeAssetUoW()
    app.dependency_overrides[asset_repository] = lambda: r
    app.dependency_overrides[event_bus] = lambda: e
    app.dependency_overrides[message_bus] = lambda: bootstrap(uow)
    app.dependency_overrides[unit_of_work_class] = lambda: lambda: uow
    app.dependency_overrides[get_active_user_token] = active_user_token
    yield TestClient(app)


def create_asset(client: TestClient, num: int, uids: List[str]):
    asset = AssetCreate(
        title=f"Asset number {num}",
        description=f"Description for {num}",
        owners_id=uids,
        file_type=f"Type of {num}",
        file_name=f"file_of_{num}.jpg",
    )
    response = client.post(ASSET_ROUTE, json=asset.dict())
    return asset, response


@pytest.mark.unit
class TestRegisterAsset:
    def test_create(self, client):
        uids = [ACTIVE_USER_TOKEN.user_id]
        asset = AssetCreate(
            title=f"Asset number",
            description=f"Description for",
            owners_id=uids,
            file_type=f"Type of ",
            file_name=f"file_of_.jpg",
        )
        response = client.post(ASSET_ROUTE, json=asset.dict())

        assert response.status_code == 201
        assert "location" in response.headers.keys()

    def test_create_multiple_owners(self, client):
        uids = [ACTIVE_USER_TOKEN.user_id, "other-owner"]
        asset = AssetCreate(
            title=f"Asset number",
            description=f"Description for",
            owners_id=uids,
            file_type=f"Type of ",
            file_name=f"file_of_.jpg",
        )
        response = client.post(ASSET_ROUTE, json=asset.dict())
        assert response.status_code == 201

    def test_cannot_create_if_not_owner(self, client):
        uids = ["another user id"]
        asset = AssetCreate(
            title=f"Asset number",
            description=f"Description for",
            owners_id=uids,
            file_type=f"Type of ",
            file_name=f"file_of_.jpg",
        )
        response = client.post(ASSET_ROUTE, json=asset.dict())
        assert response.status_code == 400


@pytest.mark.unit
class TestGetAssets:
    def test_user_assets(self, client):
        _, r1 = create_asset(client, 0, [ACTIVE_USER_TOKEN.user_id])
        aid1 = r1.headers["location"].split("/")[-1]

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
            client, 1, ["other-user", ACTIVE_USER_TOKEN.user_id]
        )
        aid2 = r2.headers["location"].split("/")[-1]

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
        a, r1 = create_asset(client, 0, [ACTIVE_USER_TOKEN.user_id])
        aid1 = r1.headers["location"].split("/")[-1]
        response = client.get(ASSET_ROUTE + "/" + aid1)
        assert response.status_code == 200
        resp = response.json()
        assert resp["id"] == aid1
        assert resp["description"] == a.description
        assert resp["file_name"] == a.file_name
        assert resp["file_type"] == a.file_type
        for owner in a.owners_id:
            assert True in (owner in oid for oid in resp["owners_id"])
        assert resp["title"] == a.title

    def test_non_existing_asset_gives_unauthorized(self, client):
        response = client.get(ASSET_ROUTE + "/random-asset-id")
        assert response.status_code == 401

    def test_get_multiple_owners_asset(self, client):
        owners = ["other_owner", ACTIVE_USER_TOKEN.user_id]
        _, r1 = create_asset(client, 0, owners)
        aid1 = r1.headers["location"].split("/")[-1]
        response = client.get(ASSET_ROUTE + "/" + aid1)
        assert response.status_code == 200
