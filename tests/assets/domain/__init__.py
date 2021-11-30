from typing import Any, Dict

import pytest

from kpm.assets.domain.entity import Asset, FileData
from kpm.shared.domain import AssetId, UserId

DataType = Dict[str, Any]


@pytest.fixture
def valid_asset() -> DataType:
    yield {
        "id": AssetId("as092092"),
        "owners_id": [UserId("userid")],
        "file": FileData(
            name="file.jpg",
            location="some_place_under_the_sea",
            type="type",
        ),
        "title": "asset title",
        "description": "description",
    }


@pytest.fixture
def asset(valid_asset) -> Asset:
    yield Asset(**valid_asset)
