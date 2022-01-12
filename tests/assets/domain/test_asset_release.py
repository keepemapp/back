import dataclasses as dc
import datetime as dt
import time

import pytest

import kpm.assets.domain.events as events
import kpm.assets.domain.model as model
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import AssetId, UserId
from kpm.shared.domain.time_utils import now_utc, to_millis
from tests.assets.domain.test_asset_creation import create_asset_cmd
from tests.assets.utils import bus


@pytest.mark.unit
class TestReleaseConditions:
    def test_true_conditon(self):
        assert model.TrueCondition().is_met()

    def test_time_condition(self):
        assert model.TrueCondition().is_met() == True
        past = to_millis(now_utc() + dt.timedelta(minutes=-10))
        past_rel = model.TimeCondition(past)
        assert past_rel.is_met()

        future_date = to_millis(now_utc() + dt.timedelta(minutes=10))
        assert model.TimeCondition(future_date).is_met() is False


@pytest.mark.unit
class TestRelease:
    def test_creation_gives_event(self):
        r = model.AssetRelease(
            name="Ar",
            description="",
            owner=UserId("u"),
            receivers=[UserId("U")],
            assets=[AssetId("a1"), AssetId("a2")],
            release_type="example",
            conditions=[model.TrueCondition()],
        )
        assert len(r.events) == 1
        assert isinstance(r.events[0], events.AssetReleaseScheduled)
        assert DomainId(r.events[0].aggregate_id) == r.id

    def test_multiple_conditions(self):
        past = to_millis(now_utc() + dt.timedelta(minutes=-10))
        future = to_millis(now_utc() + dt.timedelta(minutes=10))

        r_past = model.AssetRelease(
            name="Ar",
            description="",
            owner=UserId("u"),
            receivers=[UserId("U")],
            assets=[AssetId("a1"), AssetId("a2")],
            release_type="example",
            conditions=[model.TrueCondition(), model.TimeCondition(past)],
        )
        assert r_past.can_trigger()

        r_future = model.AssetRelease(
            name="Ar",
            description="",
            owner=UserId("u"),
            receivers=[UserId("U")],
            assets=[AssetId("a1"), AssetId("a2")],
            release_type="example",
            conditions=[model.TrueCondition(), model.TimeCondition(future)],
        )
        assert r_future.can_trigger() is False


@pytest.mark.unit
class TestAssetReleaseVisibility:
    def test_hides_assets(self, bus, create_asset_cmd):
        asset_id = "assetId"
        owner = "1"
        history = [
            dc.replace(create_asset_cmd, asset_id=asset_id, owners_id=[owner]),
            events.AssetReleaseScheduled(
                aggregate_id="none",
                re_conditions={},
                re_type="",
                owner=owner,
                assets=[asset_id],
                receivers=[owner],
            ),
        ]

        for msg in history:
            bus.handle(msg)

        with bus.uows.get(model.Asset) as uow:
            assert not uow.repo.find_by_id(AssetId(asset_id))
            assert len(uow.repo.find_by_ids([AssetId(asset_id)])) == 0
            assets = uow.repo.all()
            asset = [a for a in assets if a.id.id == asset_id][0]
            assert not asset.is_visible()

    def test_cancellation_returns_visibility(self, bus, create_asset_cmd):
        # Given
        asset_id = "assetId"
        owner = "1"
        receiver = "2"
        release_id = "123"
        bus.handle(
            dc.replace(create_asset_cmd, asset_id=asset_id, owners_id=[owner])
        )
        release = model.AssetRelease(
            id=DomainId(release_id),
            name="",
            description="",
            owner=UserId(owner),
            receivers=[UserId(receiver)],
            conditions=[model.TrueCondition()],
            release_type="dummy",
            assets=[AssetId(asset_id)],
        )
        with bus.uows.get(model.AssetRelease) as uow:
            uow.repo.put(release)
            uow.commit()
        for e in release.events:
            bus.handle(e)

        # When
        with bus.uows.get(model.AssetRelease) as uow:
            r: model.AssetRelease = uow.repo.get(DomainId(release_id))
            r.cancel()
            uow.commit()
        for e in r.events:
            bus.handle(e)

        # Then
        with bus.uows.get(model.Asset) as uow:
            a: model.Asset = uow.repo.find_by_id(AssetId(asset_id))
            assert a.is_visible()
            assert len(a.owners_id) == 1
            assert a.owners_id[0] == UserId(owner)

        with bus.uows.get(model.AssetRelease) as uow:
            rs = uow.repo.user_past_releases(UserId(owner))
            assert len(rs) == 1
            r: model.AssetRelease = rs[0]
            assert r.is_past()

    def test_release(self, bus, create_asset_cmd):
        # Given
        asset_id = "assetId"
        owner = "1"
        receiver = "2"
        release_id = "123"
        bus.handle(
            dc.replace(create_asset_cmd, asset_id=asset_id, owners_id=[owner])
        )
        release = model.AssetRelease(
            id=DomainId(release_id),
            name="",
            description="",
            owner=UserId(owner),
            receivers=[UserId(receiver)],
            conditions=[model.TrueCondition()],
            release_type="dummy",
            assets=[AssetId(asset_id)],
        )
        with bus.uows.get(model.AssetRelease) as uow:
            uow.repo.put(release)
            uow.commit()
        for e in uow.collect_new_events():
            bus.handle(e)

        # When
        with bus.uows.get(model.AssetRelease) as uow:
            r: model.AssetRelease = uow.repo.get(DomainId(release_id))
            r.release()
            uow.commit()
        for e in uow.collect_new_events():
            bus.handle(e)

        # Then
        with bus.uows.get(model.Asset) as uow:
            a: model.Asset = uow.repo.find_by_id(AssetId(asset_id))
            assert a.is_visible()
            assert len(a.owners_id) == 1
            assert a.owners_id[0] == UserId("2")

        with bus.uows.get(model.AssetRelease) as uow:
            rs = uow.repo.user_past_releases(UserId(owner))
            assert len(rs) == 1
            r: model.AssetRelease = rs[0]
            assert r.is_past()

    def test_asset_visibility_idempotent(self, bus, create_asset_cmd):
        asset_id = "assetId"
        owner = "1"
        release_id = "123"
        scheduled = events.AssetReleaseScheduled(
            aggregate_id=release_id,
            re_conditions={},
            re_type="",
            owner=owner,
            assets=[asset_id],
            receivers=[owner],
        )
        time.sleep(0.005)
        canceled = events.AssetReleaseCanceled(
            aggregate_id=release_id, assets=[asset_id]
        )

        history = [
            dc.replace(create_asset_cmd, asset_id=asset_id, owners_id=[owner]),
            canceled,
            scheduled,
        ]

        for msg in history:
            bus.handle(msg)

        with bus.uows.get(model.Asset) as uow:
            a = uow.repo.find_by_id(AssetId(asset_id))
            assert a.is_visible()
