import pathlib
from os.path import join
from typing import List

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from kpm.assets.entrypoints.fastapi.dependencies import message_bus
from kpm.assets.entrypoints.fastapi.v1 import assets_router
from kpm.assets.entrypoints.fastapi.v1.schemas import AssetCreate
from kpm.settings import settings as s
from kpm.shared.entrypoints.auth_jwt import AccessToken
from kpm.shared.entrypoints.fastapi.dependencies import get_access_token
from tests.assets.utils import bus

ASSET_ROUTE: str = s.API_V1.concat(s.API_ASSET_PATH).prefix
ACTIVE_USER_TOKEN = AccessToken(subject="uid")


def active_user_token():
    return ACTIVE_USER_TOKEN


@pytest.fixture
def client(bus) -> TestClient:
    app = FastAPI(
        title="MyHeritage User test",
    )
    app.include_router(assets_router)

    app.dependency_overrides[message_bus] = lambda: bus
    app.dependency_overrides[get_access_token] = active_user_token
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
        uids = [ACTIVE_USER_TOKEN.subject]
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
        uids = [ACTIVE_USER_TOKEN.subject, "other-owner"]
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
        _, r1 = create_asset(client, 0, [ACTIVE_USER_TOKEN.subject])
        aid1 = r1.headers["location"].split("/")[-2].split("?")[0]

        response = client.get(
            s.API_V1.concat(s.API_USER_PATH).prefix
            + "/me"
            + s.API_ASSET_PATH.prefix
        )
        assert response.status_code == 200
        json = response.json()
        assert len(json["items"]) == 1

        # Second asset
        _, r2 = create_asset(
            client, 1, ["other-user", ACTIVE_USER_TOKEN.subject]
        )
        aid2 = r2.headers["location"].split("/")[-2].split("?")[0]

        response = client.get(
            s.API_V1.concat(s.API_USER_PATH).prefix
            + "/me"
            + s.API_ASSET_PATH.prefix
        )
        assert response.status_code == 200
        json = response.json()
        assert len(json["items"]) == 2
        assert [a.get("id").split("?")[0] for a in json["items"]] == [
            aid1,
            aid2,
        ]

    def test_get_individual_asset(self, client):
        a, r1 = create_asset(client, 0, [ACTIVE_USER_TOKEN.subject])
        aid1 = r1.headers["location"].split("/")[-2].split("?")[0]
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
        owners = ["other_owner", ACTIVE_USER_TOKEN.subject]
        _, r1 = create_asset(client, 0, owners)
        aid1 = r1.headers["location"].split("/")[-2]
        response = client.get(ASSET_ROUTE + "/" + aid1)
        assert response.status_code == 200


@pytest.mark.unit
class TestUploadAsset:
    def test_upload(self, client):
        # Setup
        uids = [ACTIVE_USER_TOKEN.subject]
        asset = AssetCreate(
            title=f"Asset number",
            description=f"Description for",
            owners_id=uids,
            file_type=f"",
            file_name=f"test_uploaded_file.txt",
        )
        response = client.post(ASSET_ROUTE, json=asset.dict())
        upload_loc = s.API_V1.concat(response.headers["location"]).path()
        cwd = pathlib.Path(__file__).parent.resolve()
        with open(join(cwd, "resources", "test_uploaded_file.txt"), "rb") as f:
            upload = client.post(upload_loc, files={"file": f})
        assert upload.status_code == 201
        assert upload.headers["location"] in upload_loc

        res = client.get(s.API_V1.concat(upload.headers["location"]).path())
        assert res.status_code == 200
        with open(join(cwd, "resources", "test_uploaded_file.txt"), "rb") as f:
            assert f.read() == res._content
