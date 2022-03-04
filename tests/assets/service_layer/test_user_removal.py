import pytest

import kpm.assets.domain.commands as cmds
from kpm.assets.domain import Asset, AssetRelease
from kpm.assets.domain.repositories import (
    AssetReleaseRepository,
    AssetRepository,
)
from kpm.settings import settings as s
from kpm.shared.domain.model import RootAggState, UserId
from kpm.shared.domain.time_utils import from_now_ms
from kpm.users.domain.events import UserRemoved
from kpm.users.domain.model import Keep
from tests.assets.domain import *
from tests.assets.entrypoints.fastapi.v1.fixtures import USER_TOKEN
from tests.assets.utils import bus

USER = "user_to_remove"
USER_ID = UserId(id=USER)


@pytest.mark.unit
class TestUserRemovedHandlers:
    @staticmethod
    @pytest.fixture
    def populated_bus(bus, asset, asset2, release1, release2):
        asset.owners_id = [USER_ID]
        asset2.owners_id = [USER_ID]
        release1.owner = USER_ID
        release2.owner = USER_ID
        release1.events = release2.events = []
        with bus.uows.get(Asset) as uow:
            repo: AssetRepository = uow.repo
            repo.create(asset)
            repo.create(asset2)
            uow.commit()

        with bus.uows.get(AssetRelease) as uow:
            repo: AssetReleaseRepository = uow.repo
            repo.put(release1)
            repo.put(release2)
            uow.commit()

        yield bus

    def test_keeps_are_removed_when_user_deleted(self, populated_bus):
        # When
        populated_bus.handle(
            UserRemoved(aggregate_id=USER, by="", reason="reason")
        )

        # Then
        with populated_bus.uows.get(Asset) as uow:
            repo: AssetRepository = uow.repo
            for a in repo.all():
                assert a.state == RootAggState.REMOVED

        with populated_bus.uows.get(AssetRelease) as uow:
            repo: AssetReleaseRepository = uow.repo
            for ar in repo.all():
                assert ar.state == RootAggState.REMOVED
