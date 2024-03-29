import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pytest

from kpm.assets.adapters.memrepo import MemoryAssetRepository
from kpm.assets.adapters.mongo.repository import AssetMongoRepo, \
    AssetReleaseMongoRepo
from kpm.assets.domain import model
from kpm.assets.domain.model import AssetRelease
from kpm.assets.domain.repositories import AssetReleaseRepository
from kpm.assets.service_layer import COMMAND_HANDLERS, EVENT_HANDLERS
from kpm.shared.adapters.mongo import MongoUoW
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import FINAL_STATES, AssetId, UserId
from kpm.shared.entrypoints import bootstrap
from kpm.shared.log import logger
from kpm.shared.service_layer.message_bus import UoWs
from kpm.users.domain.model import Keep
from tests.shared.utils import TestUoW
from tests.users.utils import TestKeepRepository
from tests.users.adapters.mongo.test_repository import mongo_client


class TestAssetRepository(MemoryAssetRepository):
    def clean_all(self):
        self._repo.clear()
        self._owner_index.clear()

    def commit(self) -> None:
        pass


Releases = Dict[DomainId, AssetRelease]
OwnerReleaseIndex = Dict[UserId, List[DomainId]]


class TestReleaseRepo(AssetReleaseRepository):
    def __init__(
        self,
    ):
        super().__init__()
        self._repo: Releases = {}

    def put(self, release: AssetRelease):
        self._repo[release.id] = release
        self._seen.add(release)

    def get(self, release_id: DomainId) -> Optional[AssetRelease]:
        return self._repo.get(release_id)

    def exists(self, owner: UserId, name: str, assets: List[AssetId]) -> bool:
        for r in self.all():
            if (
                r.owner == owner
                and r.name == name
                and r.state not in FINAL_STATES
                and any(a in r.assets for a in assets)
            ):
                return True
        return False

    def all(self) -> List[AssetRelease]:
        return list(self._repo.values())

    def user_active_releases(self, user_id: UserId) -> List[AssetRelease]:
        result = []
        for _, r in self._repo.items():
            if r.is_active() and r.owner == user_id:
                result.append(r)
        return result

    def user_past_releases(self, user_id: UserId) -> List[AssetRelease]:
        result = []
        for _, r in self._repo.items():
            if r.is_past() and r.owner == user_id:
                result.append(r)
        return result


uows = {
    "asset_uow": TestUoW(TestAssetRepository),
    "release_uow": TestUoW(TestReleaseRepo),
}


@pytest.fixture
def bus():
    """Init test bus for passing it to tests"""
    return bootstrap.bootstrap(
        uows=UoWs(
            {
                model.Asset: TestUoW(TestAssetRepository),
                model.AssetRelease: TestUoW(TestReleaseRepo),
                Keep: TestUoW(TestKeepRepository),
            }
        ),
        event_handlers=EVENT_HANDLERS,
        command_handlers=COMMAND_HANDLERS,
    )


@pytest.fixture
def mongo_bus(mongo_client):
    """Init test bus for passing it to tests"""
    db = "assets_" + "".join(random.choice("smiwysndkajsown") for _ in range(5))
    logger.debug(f"Using db '{db}'", component="test")
    yield bootstrap.bootstrap(
        uows=UoWs(
            {
                model.Asset: MongoUoW(AssetMongoRepo, mongo_db=db),
                model.AssetRelease: MongoUoW(AssetReleaseMongoRepo, mongo_db=db),
                Keep: TestUoW(TestKeepRepository),
            }
        ),
        event_handlers=EVENT_HANDLERS,
        command_handlers=COMMAND_HANDLERS,
    )
    with mongo_client as client:
        client.drop_database(db)
