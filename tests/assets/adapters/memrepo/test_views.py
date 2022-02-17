import copy
import dataclasses

import pytest

from kpm.assets.adapters.memrepo import views_asset
from kpm.assets.domain.model import Asset
from kpm.shared.domain.model import AssetId
from tests.assets.domain import asset, valid_asset
from tests.assets.utils import bus


def add_asset_to_bus(asset: Asset, bus):
    with bus.uows.get(Asset) as uow:
        uow.repo.create(asset)


@pytest.fixture
def bus_with_asset(asset, bus):
    add_asset_to_bus(asset, bus)
    yield bus


@pytest.mark.unit
class TestMemoryAssetViews:
    def test_asset_to_python_dict(self, asset):
        r = views_asset.asset_to_flat_dict(asset)
        assert r.get("file_type") == asset.file.type
        assert r.get("file_name") == asset.file.name
        assert r.get("id") == asset.id.id

    def test_find_by_id(self, asset, bus_with_asset):
        non_existing = views_asset.find_by_id(
            "does not exist", bus=bus_with_asset
        )
        assert not non_existing

        should_exist = views_asset.find_by_id(asset.id.id, bus=bus_with_asset)
        assert should_exist["id"] == asset.id.id

    def test_find_id_and_owner(self, asset, bus_with_asset):
        id = asset.id.id
        owner = asset.owners_id[0].id

        id_non_existing = views_asset.find_by_id_and_owner(
            "does not exist", owner, bus=bus_with_asset
        )
        assert not id_non_existing

        owner_non_existing = views_asset.find_by_id_and_owner(
            id, "owner_non_existing", bus=bus_with_asset
        )
        assert not owner_non_existing

        should_exist = views_asset.find_by_id_and_owner(
            id, owner, bus=bus_with_asset
        )
        assert should_exist["id"] == asset.id.id

    def test_asset_type_filter(self, asset, bus_with_asset):
        ftype = asset.file.type
        owner = asset.owners_id[0].id

        # Then
        same_type = views_asset.find_by_ownerid(
            owner, bus=bus_with_asset, asset_types=[ftype]
        )
        assert len(same_type) == 1

        different_type = views_asset.find_by_ownerid(
            owner, bus=bus_with_asset, asset_types=["another type"]
        )
        assert len(different_type) == 0

    def test_order(self, asset, bus_with_asset, valid_asset):
        valid_asset["id"] = AssetId("secondAsset")
        valid_asset["title"] = "zzzzzzzz"
        second_asset = Asset(**valid_asset)
        add_asset_to_bus(second_asset, bus_with_asset)

        asc = views_asset.all_assets(order_by="title", bus=bus_with_asset)
        for a, b in zip(asc, [asset, second_asset]):
            assert a.get("title") == b.title

        desc = views_asset.all_assets(
            order_by="title", order="desc", bus=bus_with_asset
        )
        for a, b in zip(desc, [second_asset, asset]):
            assert a.get("title") == b.title

        with pytest.raises(AttributeError):
            views_asset.all_assets(order_by="non existing", bus=bus_with_asset)
