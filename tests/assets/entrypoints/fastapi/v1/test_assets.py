import pathlib
from os.path import join
from typing import List

from kpm.assets.domain.commands import CreateAsset
from kpm.assets.entrypoints.fastapi.v1.schemas import (
    AssetCreate,
    AssetUpdatableFields,
)
from kpm.settings import settings as s
from tests.assets.entrypoints.fastapi.v1.fixtures import *

ASSET_ROUTE: str = s.API_V1.concat(s.API_ASSET_PATH).path()
ASSET_ME_PATH: str = s.API_V1.concat("me", s.API_ASSET_PATH).path()


def create_asset(
    client: TestClient, num: int, uids: List[str] = None, bookmark: bool = True
):
    asset = AssetCreate(
        title=f"Asset number {num}",
        description=f"Description for {num}",
        owners_id=uids,
        file_type=f"Type of {num}",
        file_name=f"file_of_{num}.jpg",
        file_size_bytes=123333,
        bookmarked=bookmark,
        tags=["family"],
    )
    response = client.post(ASSET_ROUTE, json=asset.dict())
    assert response.status_code == 201
    return asset, response


def query_all(client, query_params=""):
    return client.get(s.API_V1.concat(s.API_ASSET_PATH).path() + query_params)


def query_uas(client, query_params=""):
    return client.get(
        s.API_V1.concat("/me", s.API_ASSET_PATH).path() + query_params
    )


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
            file_size_bytes=12323,
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
            file_size_bytes=12323,
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
            file_size_bytes=12323,
        )
        response = user_client.post(ASSET_ROUTE, json=asset.dict())
        assert response.status_code == 400


@pytest.mark.unit
class TestGetAssets:
    def test_user_assets(self, user_client):
        _, r1 = create_asset(user_client, 0, [USER_TOKEN.subject])
        aid1 = r1.headers["location"].split("/")[-2].split("?")[0]

        response = user_client.get(
            s.API_V1.concat("/me", s.API_ASSET_PATH).path()
        )
        assert response.status_code == 200
        json = response.json()
        assert len(json["items"]) == 1

        # Second asset
        _, r2 = create_asset(
            user_client, 1, ["other-user", USER_TOKEN.subject]
        )
        aid2 = r2.headers["location"].split("/")[-2].split("?")[0]

        response = query_uas(user_client)
        assert response.status_code == 200
        json = response.json()
        assert len(json["items"]) == 2
        assert [a.get("id").split("?")[0] for a in json["items"]] == [
            aid1,
            aid2,
        ]

    def test_assets_sorting(self, user_client, admin_client):
        _, r1 = create_asset(user_client, 0)
        aid1 = r1.headers["location"].split("/")[-2].split("?")[0]
        _, r2 = create_asset(user_client, 1)
        aid2 = r2.headers["location"].split("/")[-2].split("?")[0]

        # When
        response = query_uas(user_client, "?order_by=title&order=desc")
        assert response.status_code == 200
        # Then
        items = response.json()["items"]
        for r, aid in zip(items, [aid2, aid1]):
            assert r["id"] == aid

        # When
        response = query_all(admin_client, "?order_by=title&order=desc")
        assert response.status_code == 200
        # Then
        items = response.json()["items"]
        for r, aid in zip(items, [aid2, aid1]):
            assert r["id"] == aid

    def test_bookmarked_search(self, user_client, admin_client):
        create_asset(user_client, 0, bookmark=True)
        create_asset(user_client, 1, bookmark=False)
        create_asset(user_client, 2, bookmark=False)

        response = query_uas(user_client, "?bookmarked=1")
        assert len(response.json()["items"]) == 1
        response = query_uas(user_client, "?bookmarked=true")
        assert len(response.json()["items"]) == 1
        response = query_uas(user_client, "?bookmarked=false")
        assert len(response.json()["items"]) == 2
        response = query_uas(user_client, "")
        assert len(response.json()["items"]) == 3

        response = query_all(admin_client, "?bookmarked=1")
        assert len(response.json()["items"]) == 1
        response = query_all(admin_client, "?bookmarked=true")
        assert len(response.json()["items"]) == 1
        response = query_all(admin_client, "?bookmarked=false")
        assert len(response.json()["items"]) == 2
        response = query_all(admin_client, "")
        assert len(response.json()["items"]) == 3

    invalid_params = [
        "?order_by=title;",
        "?order_by=title--",
        "?order_by=title'",
        '?order_by=title"',
    ]

    @pytest.mark.parametrize("qp", invalid_params)
    def test_asset_sorting_attacks(self, qp, user_client, admin_client):
        r = query_uas(user_client, qp)
        assert r.status_code == 422

        r = query_all(admin_client, qp)
        assert r.status_code == 422

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
        assert resp["bookmarked"]
        assert not resp["extra_private"]
        assert resp["tags"] == ["family"]
        assert len(resp["people"]) == 0

    def test_non_existing_asset_gives_unauthorized(self, user_client):
        response = user_client.get(ASSET_ROUTE + "/random-asset-id")
        assert response.status_code == 403

    def test_get_multiple_owners_asset(self, user_client):
        owners = ["other_owner", USER_TOKEN.subject]
        _, r1 = create_asset(user_client, 0, owners)
        aid1 = r1.headers["location"].split("/")[-2]
        response = user_client.get(ASSET_ROUTE + "/" + aid1)
        assert response.status_code == 200

    def test_remove_asset(self, user_client):
        owners = [USER_TOKEN.subject]
        _, r1 = create_asset(user_client, 0, owners)
        aid1 = r1.headers["location"].split("/")[-2]

        response = user_client.delete(ASSET_ROUTE + "/" + aid1)
        assert response.status_code == 200

        response = user_client.get(ASSET_ROUTE + "/" + aid1)
        assert response.status_code == 403


@pytest.mark.unit
class TestUpdateAsset:
    @pytest.mark.parametrize(
        "updates",
        [
            {"title": "newtitle"},
            {"description": "newdescription"},
            {"tags": ["tag1", "tag2"]},
            {"people": ["user1", "sdewe"]},
            {"extra_private": True},
            {"extra_private": False},
            {"bookmarked": True},
            {"location": "some time", "created_date": "some place"},
        ],
    )
    def test_update_title(self, user_client, updates):
        _, r1 = create_asset(user_client, 0, [USER_TOKEN.subject])
        aid1 = r1.headers["location"].split("/")[-2].split("?")[0]

        # When
        update = AssetUpdatableFields(**updates)
        user_client.patch(ASSET_ROUTE + "/" + aid1, json=update.dict())

        # Then
        final_asset = user_client.get(ASSET_ROUTE + "/" + aid1).json()
        for field, value in updates.items():
            if isinstance(value, list):
                assert set(final_asset[field]) == set(value)
            else:
                assert final_asset[field] == value

    def test_remove_tags(self, user_client):
        _, r1 = create_asset(user_client, 0, [USER_TOKEN.subject])
        aid1 = r1.headers["location"].split("/")[-2].split("?")[0]
        update = AssetUpdatableFields(tags=["tag1", "tag2"])
        user_client.patch(ASSET_ROUTE + "/" + aid1, json=update.dict())

        # When
        update = AssetUpdatableFields(tags=[])
        user_client.patch(ASSET_ROUTE + "/" + aid1, json=update.dict())

        # Then
        final_asset = user_client.get(ASSET_ROUTE + "/" + aid1).json()
        assert set(final_asset["tags"]) == set([])

    def test_remove_description(self, user_client):
        _, r1 = create_asset(user_client, 0, [USER_TOKEN.subject])
        aid1 = r1.headers["location"].split("/")[-2].split("?")[0]
        some_descr = AssetUpdatableFields(description="some_description")
        user_client.patch(ASSET_ROUTE + "/" + aid1, json=some_descr.dict())

        # When
        no_descr = AssetUpdatableFields(description="")
        user_client.patch(ASSET_ROUTE + "/" + aid1, json=no_descr.dict())

        # Then
        final_asset = user_client.get(ASSET_ROUTE + "/" + aid1).json()
        assert final_asset["description"] == ""


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
                file_size_bytes=23123,
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


class TestSummaryEndpoints:
    @staticmethod
    def create_asset(owners, tags=None):
        if tags is None:
            tags = list()

        return CreateAsset(
            title="1",
            owners_id=owners,
            file_type="",
            file_name="",
            file_size_bytes=1,
            tags=tags,
        )

    def test_tag_cloud(self, bus, user_client):
        ows = [USER_TOKEN.subject]

        setup = [
            self.create_asset(owners=ows, tags=["pizza", "with", "pineapple"]),
            self.create_asset(owners=ows, tags=["pizza", "pineapple", "good"]),
            self.create_asset(owners=ows, tags=["cheese", "pizza"]),
            self.create_asset(owners=["bruh"], tags=["vegan", "pizza"]),
        ]
        for cmd in setup:
            bus.handle(cmd)

        resp = user_client.get(ASSET_ME_PATH + "/tag-cloud")
        assert resp.status_code == 200
        tags_freq = resp.json()
        assert "vegan" not in tags_freq.keys()
        assert tags_freq["pizza"] == 3
        assert tags_freq["pineapple"] == 2
        for t in ["cheese", "with", "good"]:
            assert tags_freq[t] == 1
