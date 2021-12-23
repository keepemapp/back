import datetime as dt

import pytest

from kpm.assets.domain.commands import AssetOwnershipChanged
from kpm.assets.domain.model import (Asset, AssetOwnershipException,
                                     AssetTitleException, EmptyOwnerException)
from kpm.shared.domain import DomainId, IdTypeException
from kpm.shared.domain.model import AssetId, UserId
from kpm.shared.domain.time_utils import now_utc, now_utc_millis, to_millis
from tests.assets.domain import asset, valid_asset


@pytest.mark.unit
class TestAssetModel:
    invalid_titles = [
        "",
        ".a2c",
        "c/sc",
        "this title is too long and should now be allowed",
        "  ",
        "#2sd",
        "*invalid initial char",
    ]

    @pytest.mark.parametrize("title", invalid_titles)
    def test_invalid_titles(self, valid_asset, title):
        valid_asset["title"] = title
        with pytest.raises(AssetTitleException):
            Asset(**valid_asset)

    valid_titles = [
        "Asset",
        "a2",
        "My asset",
        "0's",
        "à ú",
        "Is this?",
        "sds[sd]",
        "sd¡",
    ]

    @pytest.mark.parametrize("title", valid_titles)
    def test_valid_titles(self, valid_asset, title):
        valid_asset["title"] = title
        a = Asset(**valid_asset)
        assert a.title == title

    def test_valid_user_ids(self, valid_asset):
        valid_asset["owners_id"] = [UserId("3232"), UserId("11112")]
        a = Asset(**valid_asset)
        assert a.owners_id == valid_asset["owners_id"]

    def test_owners_cannot_be_empty(self, valid_asset):
        valid_asset["owners_id"] = []
        with pytest.raises(EmptyOwnerException):
            Asset(**valid_asset)

    invalid_uids = [
        [DomainId("1232")],
        [233343],
        ["", ""],
        [""],
        [UserId("3232"), UserId("11112"), ""],
        [UserId("3232"), UserId("11112"), AssetId("assetID")],
    ]

    @pytest.mark.parametrize("owners_id", invalid_uids)
    def test_invalid_user_ids(self, valid_asset, owners_id):
        valid_asset["owners_id"] = owners_id
        with pytest.raises(IdTypeException):
            Asset(**valid_asset)


@pytest.mark.unit
class TestAssetMethods:
    def test_visibility_change(self, asset):
        asset.hide(now_utc_millis())
        assert not asset.is_visible()

        asset.show(now_utc_millis())
        assert asset.is_visible()

    def test_ownership_change(self, asset):
        prev_owner = asset.owners_id[0]
        new_owners = [UserId("two")]
        mod_ts = now_utc_millis()
        asset.change_owner(mod_ts, prev_owner, new_owners)

        assert all(new in asset.owners_id for new in new_owners)
        assert prev_owner not in asset.owners_id

        ownership_events = [
            e for e in asset.events if isinstance(e, AssetOwnershipChanged)
        ]
        assert len(ownership_events) == 1
        assert ownership_events[0].owners == [o.id for o in asset.owners_id]
        assert ownership_events[0].timestamp == mod_ts
        assert ownership_events[0].aggregate_id == asset.id.id

    def test_cannot_change_in_past(self, asset):
        past = to_millis(now_utc() + dt.timedelta(minutes=-10))
        prev_owner = asset.owners_id[0]
        new_owners = [UserId("two")]

        asset.change_owner(past, prev_owner, new_owners)
        assert prev_owner in asset.owners_id
        assert all(new not in asset.owners_id for new in new_owners)

    def test_cannot_change_if_not_owner(self, asset):
        prev_owner = UserId("I DO NOT OWN IT")
        new_owners = [UserId("two")]
        mod_ts = now_utc_millis()

        with pytest.raises(AssetOwnershipException):
            asset.change_owner(mod_ts, prev_owner, new_owners)

    def test_change_same_owner_not_updates(self, asset):
        prev_owner = asset.owners_id[0]
        new_owners = [prev_owner]
        mod_ts = to_millis(now_utc() + dt.timedelta(minutes=10))
        asset.change_owner(mod_ts, prev_owner, new_owners)

        assert asset._modified_ts_for("owners_id") < mod_ts

    def test_not_updates_if_targets_own_it(self, asset):
        asset.owners_id = [UserId("one"), UserId("two")]

        prev_owner = asset.owners_id[0]
        new_owners = [UserId("one"), UserId("two")]
        mod_ts = to_millis(now_utc() + dt.timedelta(minutes=10))
        asset.change_owner(mod_ts, prev_owner, new_owners)

        assert asset._modified_ts_for("owners_id") < mod_ts
