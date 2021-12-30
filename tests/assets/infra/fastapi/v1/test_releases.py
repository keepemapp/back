import dataclasses as dc

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import kpm.assets.domain.commands as cmds
import kpm.assets.entrypoints.fastapi.v1.schemas.releases as schema
from kpm.assets.entrypoints.fastapi.v1 import assets_router
from kpm.settings import settings as s
from kpm.shared.entrypoints.fastapi.dependencies import message_bus
from kpm.shared.entrypoints.fastapi.jwt_dependencies import get_access_token
from tests.assets.domain.test_asset_creation import create_asset_cmd
from tests.assets.infra.fastapi.v1.fixtures import ADMIN_TOKEN
from tests.assets.utils import bus

ASSET_ROUTE: str = s.API_V1.concat(s.API_ASSET_PATH).prefix

ASSET_ID1 = "assetId1"
ASSET_ID2 = "assetId2"
ASSET_ID3 = "assetId3"
ASSET_ID4 = "assetId4"
OWNER1 = ADMIN_TOKEN.subject
OWNER2 = "OWNER2"


@pytest.mark.unit
class TestReleases:
    @staticmethod
    @pytest.fixture
    def populated_bus(bus, create_asset_cmd):
        to_cancel = cmds.CreateAssetToFutureSelf(
            assets=[ASSET_ID1],
            scheduled_date=123232,
            name="note",
            owner=OWNER1,
        )
        to_trigger = cmds.CreateAssetToFutureSelf(
            assets=[ASSET_ID1],
            scheduled_date=123232,
            name="note",
            owner=OWNER1,
        )
        setup = [
            dc.replace(
                create_asset_cmd, asset_id=ASSET_ID1, owners_id=[OWNER1]
            ),
            dc.replace(
                create_asset_cmd,
                asset_id=ASSET_ID2,
                owners_id=[OWNER1, OWNER2],
            ),
            dc.replace(
                create_asset_cmd,
                asset_id=ASSET_ID3,
                owners_id=[OWNER1, OWNER2],
            ),
            to_cancel,
            cmds.CreateAssetToFutureSelf(
                assets=[ASSET_ID2],
                scheduled_date=123232,
                name="note",
                owner=OWNER2,
            ),
            cmds.CreateAssetToFutureSelf(
                assets=[ASSET_ID3],
                scheduled_date=123232,
                name="note",
                owner=OWNER1,
            ),
            cmds.CancelRelease(aggregate_id=to_cancel.aggregate_id),
            to_trigger,
            cmds.TriggerRelease(aggregate_id=to_trigger.aggregate_id),
        ]
        for msg in setup:
            bus.handle(msg)
        yield bus

    @staticmethod
    @pytest.fixture
    def client(populated_bus) -> TestClient:
        app = FastAPI(
            title="Test",
        )
        app.include_router(assets_router)
        app.dependency_overrides[message_bus] = lambda: populated_bus
        app.dependency_overrides[get_access_token] = lambda: ADMIN_TOKEN
        yield TestClient(app)

    def test_list_users(self, client, populated_bus):
        response = client.get(
            s.API_V1.concat(s.API_USER_PATH, "/me", s.API_RELEASE).path()
        )
        releases = response.json()

        assert response.status_code == 200
        assert len(releases["items"]) == 1

    def test_list_all(self, client, populated_bus):
        response = client.get(s.API_V1.concat(s.API_RELEASE).path())
        releases = response.json()

        assert response.status_code == 200
        assert len(releases) == 4


@pytest.mark.unit
class TestFutureSelf:
    @staticmethod
    @pytest.fixture
    def populated_bus(bus, create_asset_cmd):
        setup = [
            dc.replace(
                create_asset_cmd, asset_id=ASSET_ID1, owners_id=[OWNER1]
            ),
            dc.replace(
                create_asset_cmd, asset_id=ASSET_ID2, owners_id=[OWNER2]
            ),
            dc.replace(
                create_asset_cmd,
                asset_id=ASSET_ID3,
                owners_id=[OWNER1, OWNER2],
            ),
        ]

        for msg in setup:
            bus.handle(msg)
        yield bus

    @staticmethod
    @pytest.fixture
    def client(populated_bus) -> TestClient:
        app = FastAPI(
            title="Test",
        )
        app.include_router(assets_router)
        app.dependency_overrides[message_bus] = lambda: populated_bus
        app.dependency_overrides[get_access_token] = lambda: ADMIN_TOKEN
        yield TestClient(app)

    def test_create(self, client):
        payload = schema.CreateAssetToFutureSelf(
            assets=[ASSET_ID1],
            name="Future self",
            scheduled_date=123223,
        )

        response = client.post(
            s.API_V1.concat(s.API_FUTURE_SELF).path(), json=payload.dict()
        )

        assert response.status_code == 201

        my_releases = client.get(
            s.API_V1.concat(response.headers["location"]).path()
        )
        release = my_releases.json()
        assert my_releases.status_code == 200
        assert release.get("name") == payload.name
        assert len(release.get("assets")) == 1
        assert payload.assets[0] in release.get("assets")[0]
        assert len(release.get("receivers")) == 1
        assert ADMIN_TOKEN.subject in release.get("receivers")[0]
        assert release.get("release_type") == "asset_future_self"

    def test_multiple_owners(self, client):
        payload = schema.CreateAssetToFutureSelf(
            assets=[ASSET_ID3],
            name="Multiple owners",
            scheduled_date=123223,
        )
        response = client.post(
            s.API_V1.concat(s.API_FUTURE_SELF).prefix, json=payload.dict()
        )
        assert response.status_code == 201

    def test_asset_future_different_owner_fails(self, client):
        payload = schema.CreateAssetToFutureSelf(
            assets=[ASSET_ID2],
            name="Other owner",
            scheduled_date=123223,
        )
        response = client.post(
            s.API_V1.concat(s.API_FUTURE_SELF).prefix, json=payload.dict()
        )
        assert response.status_code == 403
