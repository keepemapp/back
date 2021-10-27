from typing import Any, Dict

import pytest

from emo.assets.domain.entity.asset_repository import DuplicatedAssetException
from emo.assets.domain.usecase.create_asset import CreateAsset
from emo.shared.domain import AssetId
from tests.assets.utils import bus

DataType = Dict[str, Any]


@pytest.fixture
def create_asset_cmd():
    yield CreateAsset(
        title="Asset",
        description="Asset description",
        file_type="image",
        file_name="my_asset.jpg",
        owners_id=["owner1", "/users/owner2"],
    )


@pytest.mark.unit
class TestCreateAsset:
    def test_for_new_asset(self, create_asset_cmd, bus):
        bus.handle(create_asset_cmd)
        assert (
            bus.uow.repo.find_by_id(AssetId(create_asset_cmd.id)) is not None
        )
        assert bus.uow.committed

    def test_cannot_duplicate_same_asset(self, create_asset_cmd, bus):
        bus.handle(create_asset_cmd)
        assert (
            bus.uow.repo.find_by_id(AssetId(create_asset_cmd.id)) is not None
        )
        with pytest.raises(DuplicatedAssetException):
            bus.handle(create_asset_cmd)

    def test_asset_location(self, create_asset_cmd, bus):
        bus.handle(create_asset_cmd)
        a = bus.uow.repo.find_by_id(AssetId(create_asset_cmd.id))

        first_owner = create_asset_cmd.owners_id[0]
        asset_id = a.id.id
        assert first_owner in a.file.location
        assert asset_id in a.file.location
        assert ".enc" in a.file.location
