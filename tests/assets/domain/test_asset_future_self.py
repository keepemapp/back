import dataclasses as dc
import datetime as dt

import pytest

import kpm.assets.domain.entity.asset_release as ar
import kpm.assets.domain.usecase.asset_to_future_self as afs
from kpm.shared.domain import AssetId, UserId
from kpm.shared.domain.time_utils import current_utc, to_millis
from tests.assets.domain.test_asset_creation import create_asset_cmd
from tests.assets.utils import bus


@pytest.mark.unit
class TestAssetFutureSelf:
    def test_creates_asset_future(self, bus, create_asset_cmd):
        asset_id = "assetId"
        owner = "1"
        scheduled_date = current_utc() + dt.timedelta(minutes=10)
        history = [
            dc.replace(create_asset_cmd, asset_id=asset_id, owners_id=[owner]),
            afs.CreateAssetToFutureSelf(
                assets=[asset_id],
                scheduled_date=to_millis(scheduled_date),
                name="note",
                owner=owner,
            ),
        ]

        for msg in history:
            bus.handle(msg)

        with bus.uows.get(ar.AssetRelease) as uow:
            releases: ar.AssetReleaseRepository = uow.repo
            user_rel = releases.user_active_releases(UserId(owner))
            assert len(user_rel) == 1
            assert user_rel[0].assets == [AssetId(asset_id)]
            assert not user_rel[0].is_due()
