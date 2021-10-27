from typing import Any, Callable, Dict

import pytest

from emo.assets.domain.entity import Asset, FileData
from emo.shared.domain import AssetId, UserId
from emo.users.domain.entity.users import User
from tests.users.utils import MemoryUserRepository

DataType = Dict[str, Any]


@pytest.fixture
def valid_asset() -> DataType:
    yield {
        "id": AssetId("as092092"),
        "owners_id": [UserId("userid")],
        "created_at": 1630853189,
        "file": FileData(
            name="file.jpg",
            location="some_place_under_the_sea",
            type="type",
        ),
        "title": "asset title",
        "description": "description",
    }


@pytest.fixture
def get_asset(valid_asset) -> Asset:
    yield Asset(**valid_asset)
