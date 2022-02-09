import dataclasses as dc
import datetime as dt
import time
from typing import Optional

import pytest

import kpm.assets.domain.events as events
import kpm.assets.domain.model as model
from kpm.assets.domain.commands import CancelRelease, TriggerRelease
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import AssetId, RootAggState, UserId
from kpm.shared.domain.time_utils import now_utc, to_millis
from kpm.users.domain.model import Keep
from tests.assets.domain.test_asset_creation import create_asset_cmd
from tests.assets.utils import bus


@pytest.mark.unit
class TestReleaseConditions:
    def test_true_conditon(self):
        assert model.TrueCondition().is_met()

    def test_time_condition(self):
        assert model.TrueCondition().is_met()
        past = to_millis(now_utc() + dt.timedelta(minutes=-10))
        past_rel = model.TimeCondition(release_ts=past)
        assert past_rel.is_met()

        future_date = to_millis(now_utc() + dt.timedelta(minutes=10))
        assert model.TimeCondition(release_ts=future_date).is_met() is False


@pytest.mark.unit
class TestRelease:
    def test_creation_gives_event(self):
        r = model.AssetRelease(
            name="Ar",
            description="",
            owner=UserId(id="u"),
            receivers=[UserId(id="U")],
            assets=[AssetId(id="a1"), AssetId(id="a2")],
            release_type="example",
            bequest_type=model.BequestType.GIFT,
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
            owner=UserId(id="u"),
            receivers=[UserId(id="U")],
            assets=[AssetId("a1"), AssetId("a2")],
            release_type="example",
            bequest_type=model.BequestType.GIFT,
            conditions=[
                model.TrueCondition(),
                model.TimeCondition(release_ts=past),
            ],
        )
        assert r_past.can_trigger()

        r_future = model.AssetRelease(
            name="Ar",
            description="",
            owner=UserId(id="u"),
            receivers=[UserId(id="U")],
            assets=[AssetId(id="a1"), AssetId(id="a2")],
            release_type="example",
            bequest_type=model.BequestType.GIFT,
            conditions=[
                model.TrueCondition(),
                model.TimeCondition(release_ts=future),
            ],
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
            assert not uow.repo.find_by_id(AssetId(id=asset_id))
            assert len(uow.repo.find_by_ids([AssetId(id=asset_id)])) == 0
            assets = uow.repo.all()
            asset = [a for a in assets if a.id.id == asset_id][0]
            assert not asset.is_visible()

    def test_cancellation_returns_visibility(self, bus, create_asset_cmd):
        release = self.populate_bus_with_release(bus, create_asset_cmd)
        release_id = release.id
        asset_id = release.assets[0]
        owner = release.owner

        # When
        bus.handle(CancelRelease(aggregate_id=release_id.id))

        # Then
        with bus.uows.get(model.Asset) as uow:
            a: model.Asset = uow.repo.find_by_id(asset_id)
            assert a.is_visible()
            assert len(a.owners_id) == 1
            assert a.owners_id[0] == owner

        with bus.uows.get(model.AssetRelease) as uow:
            rs = uow.repo.user_past_releases(owner)
            assert len(rs) == 1
            r: model.AssetRelease = rs[0]
            assert r.is_past()

    def test_release(self, bus, create_asset_cmd):
        release = self.populate_bus_with_release(bus, create_asset_cmd)
        release_id = release.id
        asset_id = release.assets[0]
        owner = release.owner

        # When
        with bus.uows.get(model.AssetRelease) as uow:
            r: model.AssetRelease = uow.repo.get(release_id)
            r.trigger()
            uow.commit()
        for e in uow.collect_new_events():
            bus.handle(e)

        # Then
        with bus.uows.get(model.Asset) as uow:
            a: model.Asset = uow.repo.find_by_id(asset_id)
            assert a.is_visible()
            assert len(a.owners_id) == 1
            assert a.owners_id[0] == UserId(id="2")

        with bus.uows.get(model.AssetRelease) as uow:
            rs = uow.repo.user_past_releases(owner)
            assert len(rs) == 1
            r: model.AssetRelease = rs[0]
            assert r.is_past()

    KEEP_STATE_TO_FAIL_RELEASE = [
        None,
        RootAggState.PENDING,
        RootAggState.REMOVED,
        RootAggState.INACTIVE,
    ]

    @pytest.mark.parametrize("keep_state", KEEP_STATE_TO_FAIL_RELEASE)
    def test_cancellation_if_no_keep(self, bus, create_asset_cmd, keep_state):
        # Given
        release = self.populate_bus_with_release(
            bus, create_asset_cmd, keep_state=keep_state
        )
        release_id = release.id
        asset_id = release.assets[0]
        original_owner = release.owner
        # When
        bus.handle(TriggerRelease(aggregate_id=release_id.id))

        # Then
        with bus.uows.get(model.AssetRelease) as uow:
            r: model.AssetRelease = uow.repo.get(release_id)
            assert r.is_past()
            assert r.state == RootAggState.REMOVED
        with bus.uows.get(model.Asset) as uow:
            a: model.Asset = uow.repo.find_by_id(asset_id)
            assert a.is_visible()
            assert a.owners_id == [original_owner]

    def test_triggers_if_keep(self, bus, create_asset_cmd):
        # Given
        release = self.populate_bus_with_release(
            bus, create_asset_cmd, keep_state=RootAggState.ACTIVE
        )
        release_id = release.id
        asset_id = release.assets[0]
        # When
        bus.handle(TriggerRelease(aggregate_id=release_id.id))

        # Then
        with bus.uows.get(model.AssetRelease) as uow:
            r: model.AssetRelease = uow.repo.get(release_id)
            assert r.is_past()
        with bus.uows.get(model.Asset) as uow:
            a: model.Asset = uow.repo.find_by_id(asset_id)
            assert a.is_visible()
            assert len(a.owners_id) == 1
            assert a.owners_id[0] == UserId(id="2")

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

    @staticmethod
    def populate_bus_with_release(
        bus,
        create_asset_cmd,
        owner="1",
        receiver="2",
        release_id="123",
        keep_state: RootAggState = RootAggState.ACTIVE,
    ) -> model.AssetRelease:
        # Given
        asset_id = "assetId"
        if keep_state:
            keep_r = bus.uows.get(Keep).repo
            keep_r.put(
                Keep(
                    requester=UserId(id=owner),
                    requested=UserId(id=receiver),
                    state=keep_state,
                )
            )
            keep_r.commit()
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
            bequest_type=model.BequestType.GIFT,
            assets=[AssetId(asset_id)],
        )
        with bus.uows.get(model.AssetRelease) as uow:
            uow.repo.put(release)
            uow.commit()
        for e in uow.collect_new_events():
            bus.handle(e)
        return release