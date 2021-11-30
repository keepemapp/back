import pytest

from kpm.assets.domain.entity.asset import Asset
from kpm.assets.infra.memrepo import views_asset
from tests.assets.domain import asset, valid_asset
from tests.assets.utils import bus


@pytest.fixture
def uow_with_asset(asset, bus):
    uow = bus.uows.get(Asset)
    with uow:
        uow.repo.create(asset)
    yield uow


@pytest.mark.unit
class TestMemoryAssetViews:
    def test_asset_to_python_dict(self, asset):
        r = views_asset.asset_to_flat_dict(asset)
        print(r)
        assert r.get("file_type") == asset.file.type
        assert r.get("file_name") == asset.file.name
        assert r.get("id") == asset.id.id

    def test_find_by_id(self, asset, uow_with_asset):
        non_existing = views_asset.find_by_id("does not exist", uow_with_asset)
        assert not non_existing

        should_exist = views_asset.find_by_id(asset.id.id, uow_with_asset)
        assert should_exist["id"] == asset.id.id

    def test_find_id_and_owner(self, asset, uow_with_asset):
        id = asset.id.id
        owner = asset.owners_id[0].id

        id_non_existing = views_asset.find_by_id_and_owner(
            "does not exist", owner, uow_with_asset
        )
        assert not id_non_existing

        owner_non_existing = views_asset.find_by_id_and_owner(
            id, "owner_non_existing", uow_with_asset
        )
        assert not owner_non_existing

        should_exist = views_asset.find_by_id_and_owner(
            id, owner, uow_with_asset
        )
        assert should_exist["id"] == asset.id.id
