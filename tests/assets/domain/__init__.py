from typing import Any, Dict, Callable

import pytest

from emo.shared.domain import AssetId, UserId
from emo.assets.domain.entity import Asset
from emo.users.domain.entity.users import User
from tests.users.utils import MemoryUserRepository

DataType = Dict[str, Any]


@pytest.fixture
def valid_asset() -> DataType:
    yield {
        "id": AssetId("as092092"),
        "owners_id": [UserId("userid")],
        "created_at": 1630853189,
        "type": "type",
        "file_name": "file.jpg",
        "file_location": "some_place_under_the_sea",
        "title": "asset title",
        "description": "description",
        "conditionToLive": None,
    }
