import uuid

import pytest

from kpm.assets.adapters.memrepo import views_asset as memrepo_views
from kpm.assets.adapters.mongo import views_asset as mongo_views
from kpm.assets.domain.model import Asset
from kpm.shared.domain.model import AssetId, RootAggState, UserId
from tests.assets.domain import asset, random_asset, valid_asset, active_asset
from tests.assets.utils import bus


def add_asset_to_bus(asset: Asset, bus):
    with bus.uows.get(Asset) as uow:
        uow.repo.create(asset)


@pytest.fixture
def bus_with_asset(active_asset, bus):
    add_asset_to_bus(active_asset, bus)
    yield bus


@pytest.fixture
def random_assets():
    return [random_asset(active=True, users=["u1", "u2"]) for _ in range(50)]


VIEWS = [
    memrepo_views,
    mongo_views,
]


@pytest.mark.parametrize("views", VIEWS)
@pytest.mark.integration
class TestMemoryAssetViews:
    def test_asset_to_python_dict(self, asset, views):
        r = views.asset_to_flat_dict(asset)
        assert r.get("file_type") == asset.file.type
        assert r.get("file_name") == asset.file.name
        assert r.get("id") == asset.id.id

    def test_find_by_id(self, asset, bus_with_asset, views):
        non_existing = views.find_by_id(
            "does not exist", bus=bus_with_asset
        )
        assert not non_existing

        should_exist = views.find_by_id(asset.id.id, bus=bus_with_asset)
        assert should_exist["id"] == asset.id.id

    def test_find_id_and_owner(self, asset, bus_with_asset, views):
        id = asset.id.id
        owner = asset.owners_id[0].id

        id_non_existing = views.find_by_id_and_owner(
            "does not exist", owner, bus=bus_with_asset
        )
        assert not id_non_existing

        owner_non_existing = views.find_by_id_and_owner(
            id, "owner_non_existing", bus=bus_with_asset
        )
        assert not owner_non_existing

        should_exist = views.find_by_id_and_owner(
            id, owner, bus=bus_with_asset
        )
        assert should_exist["id"] == asset.id.id

    def test_asset_type_filter(self, active_asset, bus_with_asset, views):
        ftype = active_asset.file.type
        owner = active_asset.owners_id[0].id

        # Then
        same_type = views.find_by_ownerid(
            owner, bus=bus_with_asset, asset_types=[ftype]
        )
        assert len(same_type) == 1

        different_type = views.find_by_ownerid(
            owner, bus=bus_with_asset, asset_types=["another type"]
        )
        assert len(different_type) == 0

    def test_order(self, asset, bus_with_asset, valid_asset, views):
        valid_asset["id"] = AssetId("secondAsset")
        valid_asset["title"] = "zzzzzzzz"
        second_asset = Asset(**valid_asset)
        add_asset_to_bus(second_asset, bus_with_asset)

        asc = views.all_assets(order_by="title", bus=bus_with_asset)
        for a, b in zip(asc, [asset, second_asset]):
            assert a.get("title") == b.title

        desc = views.all_assets(
            order_by="title", order="desc", bus=bus_with_asset
        )
        for a, b in zip(desc, [second_asset, asset]):
            assert a.get("title") == b.title

        with pytest.raises(AttributeError):
            views.all_assets(order_by="non existing", bus=bus_with_asset)

            add_asset_to_bus(second_asset, bus_with_asset)

    def test_only_return_user_active_assets(self, valid_asset, bus, views):
        user_id = UserId(id=str(uuid.uuid4()))
        for state in [RootAggState.PENDING, RootAggState.ACTIVE,
                      RootAggState.REMOVED]:
            asset = Asset(**valid_asset)
            asset.owners_id = [user_id]
            asset.state = state
            asset.id = AssetId(id=str(uuid.uuid4()))
            add_asset_to_bus(asset, bus)

        user_id = asset.owners_id[0]
        # When
        result = views.find_by_ownerid(user_id=user_id.id, bus=bus)

        # Then
        assert len(result) == 1

    def test_assets_of_the_week(self, random_assets, bus, views):
        for asset in random_assets:
            add_asset_to_bus(asset, bus)

        user = random_assets[0].owners_id[0]
        user_assets_ids = [a.id.id for a in random_assets if user in a.owners_id]
        results = views.assets_of_the_week(user.id, bus)

        assert len(results) == 2
        assert all(a["id"] in user_assets_ids for a in results)

    def test_assets_summary(self, random_assets, bus, views):
        for asset in random_assets:
            add_asset_to_bus(asset, bus)

        user = random_assets[0].owners_id[0]
        size = sum([a.file.size_bytes/1024/1024 for a in random_assets
                            if user in a.owners_id])
        count = len([1 for a in random_assets if user in a.owners_id])

        results = views.user_stats(user.id, bus)

        assert results["size_mb"].pop("total") == size
        assert results["count"].pop("total") == count
        assert sum(results["size_mb"].values()) == size
        assert results.get("max_size_mb")

    def test_assets_summary_only_counts_active(self, bus,
                                               valid_asset, views):
        active = Asset(**valid_asset)
        active.id = AssetId("activeAset")
        active.state = RootAggState.ACTIVE
        add_asset_to_bus(active, bus)
        resulting_size = active.file.size_bytes / 1024 / 1024

        pending = Asset(**valid_asset)
        pending.id = AssetId("pendingAset")
        pending.state = RootAggState.PENDING
        add_asset_to_bus(pending, bus)

        removed = Asset(**valid_asset)
        removed.id = AssetId("RmAsset")
        removed.state = RootAggState.REMOVED
        add_asset_to_bus(removed, bus)

        results = views.user_stats(pending.owners_id[0].id, bus)

        # Then
        assert results["size_mb"].pop("total") == resulting_size
        assert results["count"].pop("total") == 1