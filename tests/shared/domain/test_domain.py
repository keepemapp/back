import datetime as dt

import pytest

from kpm.shared.domain.model import RootAggregate, RootAggState
from kpm.shared.domain.time_utils import now_utc, to_millis
from tests.assets.domain import asset, valid_asset


@pytest.mark.unit
class TestRootAggregate:
    def test_update_field_before_creation(self):
        agg = RootAggregate()
        past = to_millis(now_utc() + dt.timedelta(minutes=-10))
        # If we try to update something in the past, nothing is done
        agg._update_field(past, "state", RootAggState.HIDDEN)

        assert agg.state != RootAggState.HIDDEN

    def test_update_field_future(self):
        agg = RootAggregate()
        update_ts = to_millis(now_utc() + dt.timedelta(seconds=10))
        agg._update_field(update_ts, "state", RootAggState.HIDDEN)

        assert agg.state == RootAggState.HIDDEN

        second_ts = to_millis(now_utc() + dt.timedelta(seconds=20))
        agg._update_field(second_ts, "state", RootAggState.ACTIVE)

        assert agg.state == RootAggState.ACTIVE

    def test_update_field_keeps_latest_change(self):
        agg = RootAggregate()
        first_ts = to_millis(now_utc() + dt.timedelta(seconds=10))
        second_ts = to_millis(now_utc() + dt.timedelta(seconds=20))

        agg._update_field(second_ts, "state", RootAggState.ACTIVE)
        agg._update_field(first_ts, "state", RootAggState.HIDDEN)

        assert agg.state == RootAggState.ACTIVE
