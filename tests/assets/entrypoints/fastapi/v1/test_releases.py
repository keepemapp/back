import dataclasses as dc

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import kpm.assets.domain.commands as cmds
import kpm.assets.entrypoints.fastapi.v1.schemas.releases as schema
from kpm.assets.domain import AssetRelease
from kpm.assets.entrypoints.fastapi.v1 import assets_router
from kpm.settings import settings as s
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import AssetId, RootAggState, UserId
from kpm.shared.domain.time_utils import from_now_ms
from kpm.shared.entrypoints.fastapi.dependencies import message_bus
from kpm.shared.entrypoints.fastapi.jwt_dependencies import get_access_token
from kpm.users.domain.model import Keep
from tests.assets.domain.test_asset_creation import create_asset_cmd
from tests.assets.entrypoints.fastapi.v1.fixtures import (
    ADMIN_TOKEN,
    USER2_TOKEN, USER_TOKEN, ATTACKER_TOKEN
)
from tests.assets.utils import bus

ASSET_ROUTE: str = s.API_V1.concat(s.API_ASSET_PATH).prefix

ASSET_ID1 = "assetId1"
ASSET_ID2 = "assetId2"
ASSET_ID3 = "assetId3"
ASSET_ID4 = "assetId4"
ASSET_ID5 = "assetId5"
OWNER1 = USER_TOKEN.subject
OWNER2 = USER2_TOKEN.subject

PAST_TS = from_now_ms(days=-3)
FUTURE_TS = from_now_ms(days=20)


@pytest.mark.unit
class TestReleases:
    @staticmethod
    @pytest.fixture
    def populated_bus(bus, create_asset_cmd):
        keep_r = bus.uows.get(Keep).repo
        keep_r.put(
            Keep(
                requester=UserId(id=OWNER1),
                requested=UserId(id=OWNER2),
                state=RootAggState.ACTIVE,
            )
        )
        keep_r.commit()
        to_cancel = cmds.CreateAssetToFutureSelf(
            assets=[ASSET_ID1],
            scheduled_date=PAST_TS,
            name="note_cancel",
            owner=OWNER1,
        )
        to_trigger = cmds.CreateAssetToFutureSelf(
            assets=[ASSET_ID1],
            scheduled_date=PAST_TS,
            name="note_trigger",
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
            dc.replace(
                create_asset_cmd, asset_id=ASSET_ID4, owners_id=[OWNER2]
            ),
            dc.replace(
                create_asset_cmd, asset_id=ASSET_ID5, owners_id=[OWNER2]
            ),
            to_cancel,
            cmds.CreateAssetToFutureSelf(
                assets=[ASSET_ID2],
                scheduled_date=PAST_TS,
                name="note",
                owner=OWNER2,
            ),
            cmds.CreateAssetToFutureSelf(
                assets=[ASSET_ID3],
                scheduled_date=PAST_TS,
                name="note",
                owner=OWNER1,
            ),
            cmds.CreateTimeCapsule(
                assets=[ASSET_ID4],
                scheduled_date=PAST_TS,
                name="time_calsule_past",
                location="cmb",
                owner=OWNER2,
                receivers=[OWNER1],
            ),
            cmds.CreateTimeCapsule(
                assets=[ASSET_ID5],
                scheduled_date=FUTURE_TS,
                name="time_calsule_future",
                location="cmb",
                owner=OWNER2,
                receivers=[OWNER1],
            ),
            cmds.CancelRelease(aggregate_id=to_cancel.aggregate_id, by_user=to_cancel.owner),
            to_trigger,
            cmds.TriggerRelease(
                by_user=to_trigger.owner, aggregate_id=to_trigger.aggregate_id
            ),
        ]
        for msg in setup:
            bus.handle(msg)
        yield bus

    @staticmethod
    @pytest.fixture
    def admin_client(populated_bus) -> TestClient:
        app = FastAPI(
            title="Test",
        )
        app.include_router(assets_router)
        app.dependency_overrides[message_bus] = lambda: populated_bus
        app.dependency_overrides[get_access_token] = lambda: ADMIN_TOKEN
        yield TestClient(app)

    @staticmethod
    @pytest.fixture
    def client(populated_bus) -> TestClient:
        app = FastAPI(
            title="Test",
        )
        app.include_router(assets_router)
        app.dependency_overrides[message_bus] = lambda: populated_bus
        app.dependency_overrides[get_access_token] = lambda: USER_TOKEN
        yield TestClient(app)

    def test_list_users(self, client, populated_bus):
        response = client.get(s.API_V1.concat("me", s.API_LEGACY).path())
        releases = response.json()

        assert response.status_code == 200
        assert len(releases["items"]) == 1

    def test_list_all(self, admin_client, client, populated_bus):
        response = admin_client.get(s.API_V1.concat(s.API_LEGACY).path())
        releases = response.json()

        assert response.status_code == 200
        assert len(releases) == 4

        # Users cannot access this endpoint
        response = client.get(s.API_V1.concat(s.API_LEGACY).path())
        assert response.status_code == 403

    def test_incoming(self, client, populated_bus):
        response = client.get(
            s.API_V1.concat("me", s.API_LEGACY, "incoming").path()
        )
        assert response.status_code == 200
        releases = response.json()
        assert len(releases["items"]) == 2


@pytest.mark.unit
class TestTrigger:
    @staticmethod
    def client(bus, token=USER_TOKEN) -> TestClient:
        keep_r = bus.uows.get(Keep).repo
        keep_r.put(
            Keep(
                requester=UserId(id=OWNER1),
                requested=UserId(id=OWNER2),
                state=RootAggState.ACTIVE,
            )
        )
        keep_r.put(
            Keep(
                requester=UserId(id=OWNER1),
                requested=UserId(id=ADMIN_TOKEN.subject),
                state=RootAggState.ACTIVE,
            )
        )
        keep_r.put(
            Keep(
                requester=UserId(id=OWNER2),
                requested=UserId(id=ADMIN_TOKEN.subject),
                state=RootAggState.ACTIVE,
            )
        )
        keep_r.commit()
        app = FastAPI(
            title="Test",
        )
        app.include_router(assets_router)
        app.dependency_overrides[message_bus] = lambda: bus
        app.dependency_overrides[get_access_token] = lambda: token
        return TestClient(app)

    @pytest.mark.parametrize(
        "cond",
        [
            {"date": PAST_TS, "r_code": 204},
            {"date": FUTURE_TS, "r_code": 403},
        ],
    )
    def test_time_release(self, bus, create_asset_cmd, cond):
        # Given
        setup = [
            dc.replace(
                create_asset_cmd, asset_id=ASSET_ID1, owners_id=[OWNER1]
            ),
        ]
        for msg in setup:
            bus.handle(msg)
        client = self.client(bus)
        # When
        create_payload = schema.CreateAssetToFutureSelf(
            assets=[ASSET_ID1],
            scheduled_date=cond["date"],
            name="note",
        )
        r = client.post(
            s.API_V1.concat(s.API_LEGACY, s.API_FUTURE_SELF).path(),
            json=create_payload.dict(),
        )
        assert r.status_code == 201

        with bus.uows.get(AssetRelease) as uow:
            rs = uow.repo.all()
            ID = rs[0].id.id

        payload = schema.ReleaseTrigger(
            aggregate_id=ID,
        )
        response = client.post(
            s.API_V1.concat(s.API_LEGACY, ID, "trigger").path(),
            json=payload.dict(),
        )
        # Then
        assert response.status_code == cond["r_code"]
        with bus.uows.get(AssetRelease) as uow:
            r = uow.repo.get(DomainId(id=ID))
            assert r
            is_past = (cond["r_code"] // 100) == 2  # True for 2XY codes
            assert r.is_past() == is_past

    @pytest.mark.parametrize(
        "cond",
        [
            {"loc": "cmb", "guess": "cmb", "r_code": 204},
            {"loc": "cmb", "guess": "WRONG", "r_code": 403},
            {"loc": "cmb", "guess": None, "r_code": 403},
            {"loc": "cmb", "guess": "WRO  dfd3cNG", "r_code": 403},
        ],
    )
    def test_hide_and_seek_release(self, bus, create_asset_cmd, cond):
        # Given
        setup = [
            dc.replace(
                create_asset_cmd, asset_id=ASSET_ID1, owners_id=[OWNER1]
            ),
        ]
        for msg in setup:
            bus.handle(msg)
        client = self.client(bus)
        # When create
        create_payload = schema.CreateHideAndSeek(
            assets=[ASSET_ID1],
            location=cond["loc"],
            name="note",
            receivers=[OWNER1],
        )
        r = client.post(
            s.API_V1.concat(s.API_LEGACY, s.API_HIDE).path(),
            json=create_payload.dict(),
        )
        assert r.status_code == 201

        # Then we can get the result
        with bus.uows.get(AssetRelease) as uow:
            rs = uow.repo.all()
            ID = rs[0].id.id
            assert rs[0].name == "note"
            assert rs[0].assets == [AssetId(ASSET_ID1)]
        # When triggering
        payload = schema.ReleaseTrigger(geo_location=cond["guess"])
        response = client.post(
            s.API_V1.concat(s.API_LEGACY, ID, "trigger").path(),
            json=payload.dict(),
        )
        # Then
        assert response.status_code == cond["r_code"]
        with bus.uows.get(AssetRelease) as uow:
            r = uow.repo.get(DomainId(id=ID))
            assert r
            is_past = (cond["r_code"] // 100) == 2  # True for 2XY codes
            assert r.is_past() == is_past

    @pytest.mark.parametrize(
        "cond",
        [
            {"date": PAST_TS, "loc": "cmb", "guess": "cmb", "r_code": 204},
            {"date": PAST_TS, "loc": "cmb", "guess": "WRONG", "r_code": 403},
            {"date": PAST_TS, "loc": "cmb", "guess": None, "r_code": 403},
            {"date": FUTURE_TS, "loc": "cmb", "guess": "cmb", "r_code": 403},
            {"date": FUTURE_TS, "loc": "cmb", "guess": "WRONG", "r_code": 403},
        ],
    )
    def test_time_capsule(self, bus, create_asset_cmd, cond):
        # Given
        setup = [
            dc.replace(
                create_asset_cmd, asset_id=ASSET_ID1, owners_id=[OWNER1]
            ),
        ]
        for msg in setup:
            bus.handle(msg)
        client = self.client(bus)
        # When create
        create_payload = schema.CreateTimeCapsule(
            assets=[ASSET_ID1],
            location=cond["loc"],
            scheduled_date=cond["date"],
            name="note",
            receivers=[OWNER1],
        )
        r = client.post(
            s.API_V1.concat(s.API_LEGACY, s.API_TIME_CAPSULE).path(),
            json=create_payload.dict(),
        )
        assert r.status_code == 201

        # Then we can get the result
        with bus.uows.get(AssetRelease) as uow:
            rs = uow.repo.all()
            ID = rs[0].id.id
            assert rs[0].name == "note"
            assert rs[0].assets == [AssetId(ASSET_ID1)]
        # When triggering
        payload = schema.ReleaseTrigger(geo_location=cond["guess"])
        response = client.post(
            s.API_V1.concat(s.API_LEGACY, ID, "trigger").path(),
            json=payload.dict(),
        )
        # Then
        assert response.status_code == cond["r_code"]
        with bus.uows.get(AssetRelease) as uow:
            r = uow.repo.get(DomainId(id=ID))
            assert r
            is_past = (cond["r_code"] // 100) == 2  # True for 2XY codes
            assert r.is_past() == is_past

    @pytest.mark.parametrize(
        "cond",
        [
            {"date": PAST_TS, "r_code": 204},
            {"date": FUTURE_TS, "r_code": 403},
        ],
    )
    def test_transfer(self, bus, create_asset_cmd, cond):
        # Given
        setup = [
            dc.replace(
                create_asset_cmd, asset_id=ASSET_ID1, owners_id=[OWNER1]
            ),
        ]
        for msg in setup:
            bus.handle(msg)
        client = self.client(bus)
        # When
        create_payload = schema.CreateTransfer(
            assets=[ASSET_ID1],
            scheduled_date=cond["date"],
            name="note",
            receivers=[OWNER1],
        )
        r = client.post(
            s.API_V1.concat(s.API_LEGACY, s.API_TRANSFER).path(),
            json=create_payload.dict(),
        )
        assert r.status_code == 201

        with bus.uows.get(AssetRelease) as uow:
            rs = uow.repo.all()
            ID = rs[0].id.id
            assert rs[0].name == "note"
            assert rs[0].assets == [AssetId(ASSET_ID1)]

        payload = schema.ReleaseTrigger()
        response = client.post(
            s.API_V1.concat(s.API_LEGACY, ID, "trigger").path(),
            json=payload.dict(),
        )
        # Then
        assert response.status_code == cond["r_code"]
        with bus.uows.get(AssetRelease) as uow:
            r = uow.repo.get(DomainId(id=ID))
            assert r
            is_past = (cond["r_code"] // 100) == 2  # True for 2XY codes
            assert r.is_past() == is_past

    @pytest.mark.parametrize(
        "cond",
        [
            {"receivers": [OWNER1], "auth_tok": USER_TOKEN, "r_code": 204},
            {
                "receivers": [OWNER1, ADMIN_TOKEN.subject],
                "auth_tok": ADMIN_TOKEN,
                "r_code": 204,
            },
            {"receivers": [OWNER1], "auth_tok": ADMIN_TOKEN, "r_code": 403},
            {"receivers": [OWNER1], "auth_tok": ATTACKER_TOKEN, "r_code": 403},
        ],
    )
    def test_triggered_by_receiver(self, bus, create_asset_cmd, cond):
        # Given
        ID = "time_capsule"
        setup = [
            dc.replace(
                create_asset_cmd, asset_id=ASSET_ID1, owners_id=[OWNER2]
            ),
            cmds.CreateTransfer(
                aggregate_id=ID,
                assets=[ASSET_ID1],
                name="note",
                owner=OWNER2,
                receivers=cond["receivers"],
            ),
        ]
        for msg in setup:
            bus.handle(msg)
        client = self.client(bus, token=cond["auth_tok"])
        # When
        payload = schema.ReleaseTrigger()
        response = client.post(
            s.API_V1.concat(s.API_LEGACY, ID, "trigger").path(),
            json=payload.dict(),
        )
        # Then
        assert response.status_code == cond["r_code"]
        with bus.uows.get(AssetRelease) as uow:
            r = uow.repo.get(DomainId(id=ID))
            assert r
            is_past = (cond["r_code"] // 100) == 2  # True for 2XY codes
            assert r.is_past() == is_past


    @pytest.mark.parametrize(
        "cond",
        [
            {"receivers": [OWNER1], "auth_tok": USER_TOKEN, "r_code": 204},
            {
                "receivers": [OWNER1, ADMIN_TOKEN.subject],
                "auth_tok": ADMIN_TOKEN,
                "r_code": 204,
            },
            {"receivers": [OWNER1], "auth_tok": USER2_TOKEN, "r_code": 204},
            {"receivers": [OWNER1], "auth_tok": ADMIN_TOKEN, "r_code": 403},
            {"receivers": [OWNER1], "auth_tok": ATTACKER_TOKEN, "r_code": 403},
        ],
    )
    def test_declined(self, bus, create_asset_cmd, cond):
        # Given
        ID = "to_decline"
        setup = [
            dc.replace(
                create_asset_cmd, asset_id=ASSET_ID1, owners_id=[OWNER2]
            ),
            cmds.CreateTransfer(
                aggregate_id=ID,
                assets=[ASSET_ID1],
                name="note",
                owner=OWNER2,
                receivers=cond["receivers"],
            ),
        ]
        for msg in setup:
            bus.handle(msg)
        client = self.client(bus, token=cond["auth_tok"])
        # When
        response = client.delete(
            s.API_V1.concat(s.API_LEGACY, ID).path(),
        )
        # Then
        assert response.status_code == cond["r_code"]
        with bus.uows.get(AssetRelease) as uow:
            r = uow.repo.get(DomainId(id=ID))
            assert r
            is_past = (cond["r_code"] // 100) == 2  # True for 2XY codes
            assert r.is_past() == is_past

@pytest.mark.unit
class TestAssetReleasesTypes:
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
        app.dependency_overrides[get_access_token] = lambda: USER_TOKEN
        yield TestClient(app)

    def test_future_self(self, client):
        payload = schema.CreateAssetToFutureSelf(
            assets=[ASSET_ID1],
            name="Future self",
            scheduled_date=123223,
        )

        response = client.post(
            s.API_V1.concat(s.API_LEGACY, s.API_FUTURE_SELF).path(),
            json=payload.dict(),
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
        assert USER_TOKEN.subject in release.get("receivers")[0]
        assert release.get("release_type") == "asset_future_self"

    def test_multiple_owners(self, client):
        payload = schema.CreateAssetToFutureSelf(
            assets=[ASSET_ID3],
            name="Multiple owners",
            scheduled_date=123223,
        )
        response = client.post(
            s.API_V1.concat(s.API_LEGACY, s.API_FUTURE_SELF).prefix,
            json=payload.dict(),
        )
        assert response.status_code == 201

    def test_asset_future_different_owner_fails(self, client):
        payload = schema.CreateAssetToFutureSelf(
            assets=[ASSET_ID2],
            name="Other owner",
            scheduled_date=123223,
        )
        response = client.post(
            s.API_V1.concat(s.API_LEGACY, s.API_FUTURE_SELF).prefix,
            json=payload.dict(),
        )
        assert response.status_code == 403

    def test_bottle_no_date(self, client):
        payload = schema.CreateAssetInABottle(
            assets=[ASSET_ID1],
            name="Bottle",
            receivers=["/users/user1", "/users/user2"],
        )
        # When
        response = client.post(
            s.API_V1.concat(s.API_LEGACY, s.API_ASSET_BOTTLE).path(),
            json=payload.dict(),
        )
        # Then
        assert response.status_code == 201

        my_releases = client.get(
            s.API_V1.concat(response.headers["location"]).path()
        )
        release = my_releases.json()
        assert release.get("release_type") == "asset_future_self"
        assert my_releases.status_code == 200
        assert release.get("name") == payload.name
        assert len(release.get("assets")) == 1
        assert payload.assets[0] in release.get("assets")[0]
        assert len(release.get("receivers")) == 2
        assert "/users/user2" in release.get("receivers")
        assert "/users/user1" in release.get("receivers")

    def test_bottle_between_date(self, client):
        payload = schema.CreateAssetInABottle(
            assets=[ASSET_ID1],
            name="Bottle",
            receivers=["/users/user1", "/users/user2"],
            min_date=10,
            max_date=20,
        )
        # When
        response = client.post(
            s.API_V1.concat(s.API_LEGACY, s.API_ASSET_BOTTLE).path(),
            json=payload.dict(),
        )
        # Then
        my_releases = client.get(
            s.API_V1.concat(response.headers["location"]).path()
        )
        assert my_releases.status_code == 200

    def test_bottle_swapped_dates(self, client):
        payload = {
            "assets": [ASSET_ID1],
            "name": "Bottle",
            "receivers": ["/users/user1", "/users/user2"],
            "min_date": 232,
            "max_date": 20,
        }
        # When
        response = client.post(
            s.API_V1.concat(s.API_LEGACY, s.API_ASSET_BOTTLE).path(),
            json=payload,
        )
        # Then
        assert response.status_code == 422

