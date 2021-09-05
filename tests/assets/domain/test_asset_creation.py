from typing import Any, Dict

import pytest

from emo.assets.domain.entity import Asset
from emo.assets.domain.usecase.create_asset import CreateAsset
from emo.shared.domain import UserId
from tests.assets.utils import MemoryAssetRepository
from tests.utils import TestEventPublisher

DataType = Dict[str, Any]


@pytest.fixture
def valid_create_asset() -> DataType:
    repo = MemoryAssetRepository()
    repo.clean_all()  # TODO check why repo is not clean here.
    # It looks like is reusing a cached instance
    yield {
        "title": "me",
        "description": "password",
        "type": "image",
        "file_name": "myfile.png",
        "owners_id": [UserId("owner1")],
        "conditionToLive": None,
        "repository": repo,
        "message_bus": TestEventPublisher(),
    }
    repo.clean_all()


@pytest.mark.unit
class TestCreateAsset:
    def test_create_asset(self, valid_create_asset):
        c = CreateAsset(**valid_create_asset)
        assert isinstance(c.entity, Asset)

    def test_asset_location(self, valid_create_asset):
        c = CreateAsset(**valid_create_asset)
        first_owner = c.entity.owners_id[0].id
        asset_id = c.entity.id.id
        assert first_owner in c.entity.file_location
        assert asset_id in c.entity.file_location
        assert ".enc" in c.entity.file_location

    def test_event_is_published(self, valid_create_asset):
        c = CreateAsset(**valid_create_asset)
        c.execute()
        bus = valid_create_asset.get("message_bus")

        assert bus.published_event == c.event

    def test_asset_is_saved(self, valid_create_asset):
        c = CreateAsset(**valid_create_asset)
        c.execute()
        repo: MemoryAssetRepository = valid_create_asset.get("repository")
        # assert repo.all() == c.entity.id
        assert repo.find_by_id(c.entity.id) == c.entity
