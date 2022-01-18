from typing import Any, Dict
import uuid

import pytest

from kpm.assets.domain.model import Asset, FileData
from kpm.shared.domain.model import AssetId, UserId

DataType = Dict[str, Any]


@pytest.fixture
def valid_asset() -> DataType:
    yield {
        "id": AssetId(str(uuid.uuid4())),
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


@pytest.fixture
def asset2() -> Asset:
    yield Asset(**{
        "id": AssetId(str(uuid.uuid4())),
        "owners_id": [UserId("userid2")],
        "file": FileData(
            name="file2.jpg",
            location="some/place/under_the_sea",
            type="type2",
        ),
        "title": "z second asset",
        "description": "description of the second asset",
    })


__all__ = ["valid_asset", "asset", "asset2"]