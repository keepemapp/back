import pytest
import datetime as dt

from emo.assets.domain.entity import (Asset, AssetTitleException,
                                      EmptyOwnerException)
from emo.shared.domain import RootAggregate, RootAggState
from tests.assets.domain import valid_asset, asset
from emo.shared.domain.time_utils import current_utc, to_millis

@pytest.mark.unit
class TestRootAggregate:
    def test_update_field_before_creation(self):
        agg = RootAggregate()
        past = to_millis(current_utc() + dt.timedelta(minutes=-10))
        # If we try to update something in the past, nothing is done
        agg._update_field(past, "state", RootAggState.HIDDEN)

        assert agg.state != RootAggState.HIDDEN

    def test_update_field_future(self):
        agg = RootAggregate()
        update_ts = to_millis(current_utc() + dt.timedelta(seconds=10))
        agg._update_field(update_ts, "state", RootAggState.HIDDEN)

        assert agg.state == RootAggState.HIDDEN

        second_ts = to_millis(current_utc() + dt.timedelta(seconds=20))
        agg._update_field(second_ts, "state", RootAggState.ACTIVE)

        assert agg.state == RootAggState.ACTIVE

    def test_update_field_keeps_latest_change(self):
        agg = RootAggregate()
        first_ts = to_millis(current_utc() + dt.timedelta(seconds=10))
        second_ts = to_millis(current_utc() + dt.timedelta(seconds=20))

        agg._update_field(second_ts, "state", RootAggState.ACTIVE)
        agg._update_field(first_ts, "state", RootAggState.HIDDEN)

        assert agg.state == RootAggState.ACTIVE