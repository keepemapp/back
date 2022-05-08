import pytest

from kpm.assets.domain import AssetRelease, BequestType, TimeCondition
from kpm.assets.domain.repositories import AssetReleaseRepository
from kpm.settings import settings as s
from kpm.shared.domain.model import RootAggState, UserId
from kpm.shared.domain.time_utils import from_now_ms
from kpm.users.domain.model import Keep
from kpm.users.domain.repositories import KeepRepository
from tests.users.entrypoints.fastapi import ADMIN_TOKEN, USER_TOKEN, user_client
from tests.assets.utils import bus

PAST_TS = from_now_ms(days=-3)
FUTURE_TS = from_now_ms(days=20)


@pytest.mark.unit
class TestPendingActionsApi:
    @staticmethod
    @pytest.fixture
    def init_keeps(bus):
        with bus.uows.get(Keep) as uow:
            repo: KeepRepository = uow.repo
            repo.put(Keep(
                requester=UserId(USER_TOKEN.subject),
                requested=UserId(ADMIN_TOKEN.subject),
                state=RootAggState.PENDING
            ))
            repo.put(Keep(
                requester=UserId("Some random user"),
                requested=UserId(USER_TOKEN.subject),
                state=RootAggState.PENDING
            ))
            repo.put(Keep(
                requester=UserId(USER_TOKEN.subject),
                requested=UserId("otherUser"),
                state=RootAggState.ACTIVE
            ))
            repo.put(Keep(
                requester=UserId(USER_TOKEN.subject),
                requested=UserId("other2"),
                state=RootAggState.REMOVED
            ))
            repo.put(Keep(
                requester=UserId(ADMIN_TOKEN.subject),
                requested=UserId("other_user"),
                state=RootAggState.PENDING
            ))
            repo.commit()

    @staticmethod
    @pytest.fixture
    def init_legacy(bus):
        with bus.uows.get(AssetRelease) as uow:
            repo: AssetReleaseRepository = uow.repo
            repo.put(AssetRelease(
                name="Past to other one",
                assets=[],
                owner=UserId(USER_TOKEN.subject),
                receivers=[UserId("someone_else")],
                release_type="",
                bequest_type=BequestType.GIFT,
                conditions=[TimeCondition(release_ts=PAST_TS)],
                state=RootAggState.ACTIVE
            ))
            repo.put(AssetRelease(
                name="Past to himself",
                owner=UserId(USER_TOKEN.subject),
                assets=[],
                receivers=[UserId(USER_TOKEN.subject)],
                release_type="",
                bequest_type=BequestType.GIFT,
                conditions=[TimeCondition(release_ts=PAST_TS)],
                state=RootAggState.ACTIVE
            ))
            repo.put(AssetRelease(
                name="Past to himself already triggered",
                owner=UserId(USER_TOKEN.subject),
                receivers=[UserId(USER_TOKEN.subject)],
                assets=[],
                release_type="",
                bequest_type=BequestType.GIFT,
                conditions=[TimeCondition(release_ts=PAST_TS)],
                state=RootAggState.INACTIVE
            ))
            repo.put(AssetRelease(
                name="Pending to him",
                assets=[],
                owner=UserId(ADMIN_TOKEN.subject),
                receivers=[UserId(USER_TOKEN.subject)],
                release_type="",
                bequest_type=BequestType.GIFT,
                conditions=[TimeCondition(release_ts=PAST_TS)],
                state=RootAggState.ACTIVE
            ))
            repo.put(AssetRelease(
                name="Future to him",
                assets=[],
                owner=UserId(ADMIN_TOKEN.subject),
                receivers=[UserId(USER_TOKEN.subject)],
                release_type="",
                bequest_type=BequestType.GIFT,
                conditions=[TimeCondition(release_ts=FUTURE_TS)],
                state=RootAggState.ACTIVE
            ))
            repo.commit()

    def test_counts_keeps(self, bus, init_keeps, user_client):
        _ = init_keeps
        res = user_client.get(
            s.API_V1.concat(s.API_ME, "pending-actions").path(),
        )
        assert res.status_code == 200
        assert res.json()["keeps"] == 1

    def test_counts_legacy(self, bus, init_legacy, user_client):
        _ = init_legacy
        res = user_client.get(
            s.API_V1.concat(s.API_ME, "pending-actions").path(),
        )
        assert res.status_code == 200
        assert res.json()["legacy"] == 2