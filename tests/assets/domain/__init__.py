import datetime as dt
import random
import string
import uuid
from typing import Any, Dict

import pytest

from kpm.assets.domain import model
from kpm.assets.domain.model import Asset, BequestType, FileData
from kpm.shared.domain.model import AssetId, RootAggState, UserId
from kpm.shared.domain.time_utils import now_utc, to_millis

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
            size_bytes=123223,
        ),
        "title": "asset title",
        "description": "description",
    }


@pytest.fixture
def active_asset(valid_asset) -> Asset:
    valid_asset["state"] = "active"
    valid_asset["title"] = "active"
    valid_asset["id"] = AssetId(str(uuid.uuid4()))
    yield Asset(**valid_asset)


def random_asset(active=False, users=None) -> Asset:
    def random_str(len=15):
        return ''.join(random.choice(string.ascii_letters) for i in range(len))

    def random_file_type():
        types = [(".jpg", "image/jpeg"),
                 (".png", "image/png"),
                 (".mp4", "video/mp4"),
                 (".pdf", "application/pdf"),
                 ]
        return random.choice(types)

    if not users:
        users = [random_str(5) for _ in range(10)]
    file_extension, type = random_file_type()

    state = RootAggState.PENDING
    if active:
        state = RootAggState.ACTIVE
    return Asset(
        id=AssetId(str(uuid.uuid4())),
        owners_id=[UserId(random.choice(users))],
        title=random_str(),
        state=state,
        file=FileData(
            name=random_str(10)+file_extension,
            location=random_str(),
            type=type,
            size_bytes=random.randint(2*20, 2**28)
        )
    )


@pytest.fixture
def asset(valid_asset) -> Asset:
    yield Asset(**valid_asset)


@pytest.fixture
def asset2() -> Asset:
    yield Asset(
        **{
            "id": AssetId(str(uuid.uuid4())),
            "owners_id": [UserId("userid2")],
            "file": FileData(
                name="file2.jpg",
                location="some/place/under_the_sea",
                type="type2",
                size_bytes=4344332,
            ),
            "title": "z second asset",
            "description": "description of the second asset",
        }
    )


@pytest.fixture
def release1() -> model.AssetRelease:
    future = to_millis(now_utc() + dt.timedelta(minutes=10))
    return model.AssetRelease(
        name="Ar1",
        description="1",
        owner=UserId("u1"),
        receivers=[UserId("U")],
        assets=[AssetId("a11"), AssetId("a12")],
        release_type="example",
        bequest_type=BequestType.GIFT,
        conditions=[
            model.TrueCondition(),
            model.TimeCondition(release_ts=future),
            model.GeographicalCondition(location="cmb"),
        ],
    )


@pytest.fixture
def release2() -> model.AssetRelease:
    return model.AssetRelease(
        name="Ar2",
        description="2",
        owner=UserId("u2"),
        receivers=[UserId("U")],
        assets=[AssetId("a22"), AssetId("a21")],
        release_type="example",
        bequest_type=BequestType.GIFT,
        conditions=[model.TrueCondition()],
    )


__all__ = ["valid_asset", "asset", "asset2", "release1", "release2"]
