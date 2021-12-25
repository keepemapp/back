import pathlib
from os.path import join
from typing import List

from kpm.assets.entrypoints.fastapi.v1.schemas import AssetCreate
from kpm.settings import settings as s
from tests.assets.infra.fastapi.v1.fixtures import *

ASSET_ROUTE: str = s.API_V1.concat(s.API_ASSET_PATH).prefix


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
    def test_create(self, user_client):
        uids = [USER_TOKEN.subject]
        asset = AssetCreate(
            title=f"Asset number",
            description=f"Description for",
            owners_id=uids,
            file_type=f"Type of ",
            file_name=f"file_of_.jpg",
        )
        response = user_client.post(ASSET_ROUTE, json=asset.dict())

        assert response.status_code == 201
        assert "location" in response.headers.keys()

    def test_create_multiple_owners(self, user_client):
        uids = [USER_TOKEN.subject, "other-owner"]
        asset = AssetCreate(
            title=f"Asset number",
            description=f"Description for",
            owners_id=uids,
            file_type=f"Type of ",
            file_name=f"file_of_.jpg",
        )
        response = user_client.post(ASSET_ROUTE, json=asset.dict())
        assert response.status_code == 201

    def test_cannot_create_if_not_owner(self, user_client):
        uids = ["another user id"]
        asset = AssetCreate(
            title=f"Asset number",
            description=f"Description for",
            owners_id=uids,
            file_type=f"Type of ",
            file_name=f"file_of_.jpg",
        )
        response = user_client.post(ASSET_ROUTE, json=asset.dict())
        assert response.status_code == 400


@pytest.mark.unit
class TestGetAssets:
    def test_user_assets(self, user_client):
        _, r1 = create_asset(user_client, 0, [USER_TOKEN.subject])
        aid1 = r1.headers["location"].split("/")[-2].split("?")[0]

        response = user_client.get(
            s.API_V1.concat(s.API_USER_PATH).prefix
            + "/me"
            + s.API_ASSET_PATH.prefix
        )
        assert response.status_code == 200
        json = response.json()
        assert len(json["items"]) == 1

        # Second asset
        _, r2 = create_asset(
            user_client, 1, ["other-user", USER_TOKEN.subject]
        )
        aid2 = r2.headers["location"].split("/")[-2].split("?")[0]

        response = user_client.get(
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

    def test_get_individual_asset(self, user_client):
        a, r1 = create_asset(user_client, 0, [USER_TOKEN.subject])
        aid1 = r1.headers["location"].split("/")[-2].split("?")[0]
        response = user_client.get(ASSET_ROUTE + "/" + aid1)
        assert response.status_code == 200
        resp = response.json()
        assert resp["id"] == aid1
        assert resp["description"] == a.description
        assert resp["file_name"] == a.file_name
        assert resp["file_type"] == a.file_type
        for owner in a.owners_id:
            assert True in (owner in oid for oid in resp["owners_id"])
        assert resp["title"] == a.title

    def test_non_existing_asset_gives_unauthorized(self, user_client):
        response = user_client.get(ASSET_ROUTE + "/random-asset-id")
        assert response.status_code == 403

    def test_get_multiple_owners_asset(self, user_client):
        owners = ["other_owner", USER_TOKEN.subject]
        _, r1 = create_asset(user_client, 0, owners)
        aid1 = r1.headers["location"].split("/")[-2]
        response = user_client.get(ASSET_ROUTE + "/" + aid1)
        assert response.status_code == 200


@pytest.mark.unit
class TestUploadAsset:
    RESOURCES: str = join(pathlib.Path(__file__).parent.resolve(), "resources")
    GOOD_ASSET: str = join(RESOURCES, "test_uploaded_file.txt")
    BAD_ASSET: str = join(RESOURCES, "test_bad_file.txt")
    IMAGE: str = join(RESOURCES, "test_image_file.jpg")

    @pytest.fixture
    def client_w_asset(self, user_client):
        def _factory(ftype="", fname="test_uploaded_file.txt"):
            uids = [USER_TOKEN.subject]
            asset = AssetCreate(
                title=f"Asset number",
                description=f"Description for",
                owners_id=uids,
                file_type=ftype,
                file_name=fname,
            )
            response = user_client.post(ASSET_ROUTE, json=asset.dict())
            upload_loc = s.API_V1.concat(response.headers["location"]).path()
            return user_client, upload_loc

        return _factory

    def test_upload(self, client_w_asset):
        client, upload_loc = client_w_asset()
        # Uploading a file
        with open(self.GOOD_ASSET, "rb") as f:
            upload = client.post(upload_loc, files={"file": f})
        assert upload.status_code == 201
        assert upload.headers["location"] in upload_loc

        # Test file retrieved is the same
        res = client.get(s.API_V1.concat(upload.headers["location"]).path())
        assert res.status_code == 200
        with open(self.GOOD_ASSET, "rb") as f:
            assert f.read() == res._content

        # Test asset state was correctly updated
        asset_id = "/".join(upload_loc.split("/")[:5])
        updated_a = client.get(asset_id)
        assert updated_a.status_code == 200
        assert not updated_a.json().get("upload_path")
        assert updated_a.json()["state"] == "active"

    def test_wrong_file_name(self, client_w_asset):
        client, upload_loc = client_w_asset()
        # Uploading a file
        with open(self.BAD_ASSET, "rb") as f:
            upload = client.post(upload_loc, files={"file": f})
        assert upload.status_code == 400

    def test_wrong_file_type(self, client_w_asset):
        client, upload_loc = client_w_asset(ftype="random_ftype")
        # Uploading a file
        with open(self.GOOD_ASSET, "rb") as f:
            upload = client.post(upload_loc, files={"file": f})
        assert upload.status_code == 400
