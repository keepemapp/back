import pytest

from emo.assets.infra.memrepo import views
from tests.assets.domain import get_asset, valid_asset
from tests.assets.utils import FakeAssetUoW


@pytest.fixture
def uow_with_asset(get_asset) -> FakeAssetUoW:
    uow = FakeAssetUoW()
    with uow:
        uow.repo.create(get_asset)
    yield uow


@pytest.mark.unit
class TestMemoryAssetViews:
    def test_asset_to_python_dict(self, get_asset):
        r = views.asset_to_flat_dict(get_asset)
        print(r)
        assert r.get("file_type") == get_asset.file.type
        assert r.get("file_name") == get_asset.file.name
        assert r.get("id") == get_asset.id.id

    def test_find_by_id(self, get_asset, uow_with_asset):
        non_existing = views.find_by_id("does not exist", uow_with_asset)
        assert not non_existing

        should_exist = views.find_by_id(get_asset.id.id, uow_with_asset)
        assert should_exist["id"] == get_asset.id.id

    def test_find_id_and_owner(self, get_asset, uow_with_asset):
        id = get_asset.id.id
        owner = get_asset.owners_id[0].id

        id_non_existing = views.find_by_id_and_owner(
            "does not exist", owner, uow_with_asset
        )
        assert not id_non_existing

        owner_non_existing = views.find_by_id_and_owner(
            id, "owner_non_existing", uow_with_asset
        )
        assert not owner_non_existing

        should_exist = views.find_by_id_and_owner(id, owner, uow_with_asset)
        assert should_exist["id"] == get_asset.id.id
