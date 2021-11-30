import dataclasses as dc
import datetime as dt
import os
import time
from typing import Any, Dict

import pytest

import kpm.assets.domain.entity.asset_release as ar
import kpm.assets.domain.usecase.asset_to_future_self as afs
from kpm.assets.domain.entity.asset import Asset
from kpm.assets.domain.usecase.create_asset import CreateAsset
from kpm.shared.domain import AssetId, DomainId, UserId
from kpm.shared.domain.time_utils import current_utc, to_millis
from tests.assets.domain.test_asset_creation import create_asset_cmd
from tests.assets.utils import bus


@pytest.mark.unit
class TestReleaseConditions:
    def test_true_conditon(self):
        assert ar.TrueCondition().is_met()

    def test_time_condition(self):
        assert ar.TrueCondition().is_met() == True
        past = to_millis(current_utc() + dt.timedelta(minutes=-10))
        past_rel = ar.TimeCondition(past)
        assert past_rel.is_met()

        future_date = to_millis(current_utc() + dt.timedelta(minutes=10))
        assert ar.TimeCondition(future_date).is_met() is False


@pytest.mark.unit
class TestRelease:
    def test_creation_gives_event(self):
        r = ar.AssetRelease(
            name="Ar",
            description="",
            owner=UserId("u"),
            receivers=[UserId("U")],
            assets=[AssetId("a1"), AssetId("a2")],
            release_type="example",
            conditions=[ar.TrueCondition()],
        )
        assert len(r.events) == 1
        assert isinstance(r.events[0], ar.AssetReleaseScheduled)
        assert DomainId(r.events[0].aggregate_id) == r.id

    def test_multiple_conditions(self):
        past = to_millis(current_utc() + dt.timedelta(minutes=-10))
        future = to_millis(current_utc() + dt.timedelta(minutes=10))

        r_past = ar.AssetRelease(
            name="Ar",
            description="",
            owner=UserId("u"),
            receivers=[UserId("U")],
            assets=[AssetId("a1"), AssetId("a2")],
            release_type="example",
            conditions=[ar.TrueCondition(), ar.TimeCondition(past)],
        )
        assert r_past.is_due()

        r_future = ar.AssetRelease(
            name="Ar",
            description="",
            owner=UserId("u"),
            receivers=[UserId("U")],
            assets=[AssetId("a1"), AssetId("a2")],
            release_type="example",
            conditions=[ar.TrueCondition(), ar.TimeCondition(future)],
        )
        assert r_future.is_due() is False


@pytest.mark.unit
class TestAssetReleaseVisibility:
    def test_hides_assets(self, bus, create_asset_cmd):
        asset_id = "assetId"
        owner = "1"
        history = [
            dc.replace(create_asset_cmd, asset_id=asset_id, owners_id=[owner]),
            ar.AssetReleaseScheduled(
                re_conditions=[],
                re_type="",
                owner=owner,
                assets=[asset_id],
                receivers=[owner],
            ),
        ]

        for msg in history:
            bus.handle(msg)

        with bus.uows.get(Asset) as uow:
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
        release = ar.AssetRelease(
            id=DomainId(release_id),
            name="",
            description="",
            owner=UserId(owner),
            receivers=[UserId(receiver)],
            conditions=[ar.TrueCondition()],
            release_type="dummy",
            assets=[AssetId(asset_id)],
        )
        with bus.uows.get(ar.AssetRelease) as uow:
            uow.repo.put(release)
            uow.commit()
        for e in release.events:
            bus.handle(e)

        # When
        with bus.uows.get(ar.AssetRelease) as uow:
            r: ar.AssetRelease = uow.repo.get(DomainId(release_id))
            r.cancel()
            uow.commit()
        print(r.events)
        for e in r.events:
            bus.handle(e)

        # Then
        with bus.uows.get(Asset) as uow:
            a: Asset = uow.repo.find_by_id(AssetId(asset_id))
            assert a.is_visible()
            assert len(a.owners_id) == 1
            assert a.owners_id[0] == UserId(owner)

        with bus.uows.get(ar.AssetRelease) as uow:
            rs = uow.repo.user_past_releases(UserId(owner))
            assert len(rs) == 1
            r: ar.AssetRelease = rs[0]
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
        release = ar.AssetRelease(
            id=DomainId(release_id),
            name="",
            description="",
            owner=UserId(owner),
            receivers=[UserId(receiver)],
            conditions=[ar.TrueCondition()],
            release_type="dummy",
            assets=[AssetId(asset_id)],
        )
        with bus.uows.get(ar.AssetRelease) as uow:
            uow.repo.put(release)
            uow.commit()
        for e in uow.collect_new_events():
            bus.handle(e)

        # When
        with bus.uows.get(ar.AssetRelease) as uow:
            r: ar.AssetRelease = uow.repo.get(DomainId(release_id))
            r.release()
            uow.commit()
        for e in uow.collect_new_events():
            print(e)
            bus.handle(e)

        # Then
        with bus.uows.get(Asset) as uow:
            a: Asset = uow.repo.find_by_id(AssetId(asset_id))
            assert a.is_visible()
            assert len(a.owners_id) == 1
            assert a.owners_id[0] == UserId("2")

        with bus.uows.get(ar.AssetRelease) as uow:
            rs = uow.repo.user_past_releases(UserId(owner))
            assert len(rs) == 1
            r: ar.AssetRelease = rs[0]
            assert r.is_past()

    def test_asset_visibility_idempotent(self, bus, create_asset_cmd):
        asset_id = "assetId"
        owner = "1"
        release_id = "123"
        scheduled = ar.AssetReleaseScheduled(
            aggregate_id=release_id,
            re_conditions=[],
            re_type="",
            owner=owner,
            assets=[asset_id],
            receivers=[owner],
        )
        time.sleep(0.005)
        canceled = ar.AssetReleaseCanceled(
            aggregate_id=release_id, assets=[asset_id]
        )

        history = [
            dc.replace(create_asset_cmd, asset_id=asset_id, owners_id=[owner]),
            canceled,
            scheduled,
        ]

        for msg in history:
            bus.handle(msg)

        with bus.uows.get(Asset) as uow:
            a = uow.repo.find_by_id(AssetId(asset_id))
            assert a.is_visible()
