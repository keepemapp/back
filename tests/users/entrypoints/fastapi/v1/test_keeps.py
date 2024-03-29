import pytest

from kpm.settings import settings as s
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import RootAggState, UserId
from kpm.users.domain.model import Keep, User
from kpm.users.domain.repositories import KeepRepository, UserRepository
from kpm.users.entrypoints.fastapi.v1.schemas.keeps import (
    AcceptKeep,
    DeclineKeep,
    RequestKeep,
)
from tests.users.domain import active_user, valid_user
from tests.users.entrypoints.fastapi import *
from tests.users.fixtures import mongo_client

KEEP_ROUTE = s.API_V1.concat(s.API_MY_KEEPS)


@pytest.fixture
def init_users(bus, active_user):
    with bus.uows.get(User) as uow:
        repo: UserRepository = uow.repo
        active_user["id"] = UserId(ADMIN_TOKEN.subject)
        active_user["email"] = f"{ADMIN_TOKEN.subject}@email.com"
        admin = User(**active_user)
        repo.create(admin)

        active_user["id"] = UserId(USER_TOKEN.subject)
        active_user["email"] = f"{USER_TOKEN.subject}@email.com"
        user = User(**active_user)
        repo.create(user)

        active_user["id"] = UserId("anotherUser")
        active_user["email"] = "anotherUser@email.com"
        other = User(**active_user)
        repo.create(other)

        uow.commit()
    return admin, user


@pytest.mark.unit
class TestKeepsApi:
    def test_request_keep_by_id(self, init_users, admin_client, user_client):
        admin, user = init_users
        for client in (user_client, admin_client):
            start_resp = client.get(KEEP_ROUTE.path())
            assert start_resp.status_code == 200
            assert start_resp.json()["total"] == 0

        new_keep = user_client.post(
            KEEP_ROUTE.path(),
            json=RequestKeep(to_id=ADMIN_TOKEN.subject).dict(),
        )
        assert new_keep.status_code == 201

        for client in (user_client, admin_client):
            keep_resp = client.get(KEEP_ROUTE.path())
            assert keep_resp.json()["total"] == 1
            keep = keep_resp.json()["items"][0]
            assert keep["state"] == "pending"
            assert ADMIN_TOKEN.subject in keep["requested"]["id"]
            assert USER_TOKEN.subject in keep["requester"]["id"]
            assert keep["id"]
            assert keep["requested"]["public_name"] == admin.public_name
            assert keep["requester"]["public_name"] == user.public_name
            assert keep["requested"]["referral_code"] == admin.referral_code
            assert keep["requester"]["referral_code"] == user.referral_code

    def test_request_keep_by_id_noexists(self, user_client):
        new_keep = user_client.post(
            KEEP_ROUTE.path(),
            json=RequestKeep(to_id="idonotexistascode").dict(),
        )
        assert new_keep.status_code == 404

    def test_request_keep_malformed(self, user_client):
        with pytest.raises(ValueError):
            RequestKeep()

        with pytest.raises(ValueError):
            RequestKeep(to_id="sdsd", to_code="asdsd")

        with pytest.raises(ValueError):
            RequestKeep(to_id="sdsd", to_email="asdsd@email.com")

        with pytest.raises(ValueError):
            RequestKeep(to_email="sdsd@email.com", to_code="asdsd")

        with pytest.raises(ValueError):
            RequestKeep(to_id="sdsd", to_code="asdsd", to_email="some@ema.il")

        test_empty = user_client.post(
            KEEP_ROUTE.path(),
            json={},
        )
        assert test_empty.status_code == 422

        test_both = user_client.post(
            KEEP_ROUTE.path(),
            json={"to_id": "sdsd", "to_code": "asdsd"},
        )
        assert test_both.status_code == 422

    def test_request_keep_by_code_noexists(self, user_client):
        new_keep = user_client.post(
            KEEP_ROUTE.path(),
            json=RequestKeep(to_code="idonotexistascode").dict(),
        )
        assert new_keep.status_code == 404

    def test_request_keep_by_code(self, init_users, admin_client, user_client):
        admin, _ = init_users

        new_keep = user_client.post(
            KEEP_ROUTE.path(),
            json=RequestKeep(to_code=admin.referral_code).dict(),
        )
        assert new_keep.status_code == 201

        for client in (user_client, admin_client):
            keep_resp = client.get(KEEP_ROUTE.path())
            assert keep_resp.json()["total"] == 1
            keep = keep_resp.json()["items"][0]
            assert keep["state"] == "pending"
            assert ADMIN_TOKEN.subject in keep["requested"]["id"]
            assert USER_TOKEN.subject in keep["requester"]["id"]
            assert keep["id"]

    def test_request_keep_by_email(
        self, init_users, admin_client, user_client
    ):
        admin, _ = init_users

        new_keep = user_client.post(
            KEEP_ROUTE.path(),
            json=RequestKeep(to_email=admin.email).dict(),
        )
        assert new_keep.status_code == 201

        for client in (user_client, admin_client):
            keep_resp = client.get(KEEP_ROUTE.path())
            assert keep_resp.json()["total"] == 1
            keep = keep_resp.json()["items"][0]
            assert keep["state"] == "pending"
            assert ADMIN_TOKEN.subject in keep["requested"]["id"]
            assert USER_TOKEN.subject in keep["requester"]["id"]
            assert keep["id"]

    def test_attacker(self, init_users, user_client, attacker_client):
        user_client.post(
            KEEP_ROUTE.path(),
            json=RequestKeep(to_id=ADMIN_TOKEN.subject).dict(),
        )
        keep_id = user_client.get(KEEP_ROUTE.path()).json()["items"][0]["id"]

        # Try to accept with other users
        attack_r = attacker_client.put(
            KEEP_ROUTE.concat("accept").path(),
            json=AcceptKeep(keep_id=keep_id).dict(),
        )
        assert attack_r.status_code == 403
        assert (
            user_client.get(KEEP_ROUTE.path()).json()["items"][0]["state"]
            == "pending"
        )

    def test_accept_requester(self, init_users, user_client):
        user_client.post(
            KEEP_ROUTE.path(),
            json=RequestKeep(to_id=ADMIN_TOKEN.subject).dict(),
        )
        keep_id = user_client.get(KEEP_ROUTE.path()).json()["items"][0]["id"]

        # With the requester
        user_r = user_client.put(
            KEEP_ROUTE.concat("accept").path(),
            json=AcceptKeep(keep_id=keep_id).dict(),
        )
        assert user_r.status_code == 403
        assert (
            user_client.get(KEEP_ROUTE.path()).json()["items"][0]["state"]
            == "pending"
        )

    def test_accept(self, init_users, admin_client, user_client):
        user_client.post(
            KEEP_ROUTE.path(),
            json=RequestKeep(to_id=ADMIN_TOKEN.subject).dict(),
        )
        keep_id = user_client.get(KEEP_ROUTE.path()).json()["items"][0]["id"]

        # Finally, accept it
        admin_r = admin_client.put(
            KEEP_ROUTE.concat("accept").path(),
            json=AcceptKeep(keep_id=keep_id).dict(),
        )
        assert admin_r.status_code == 204
        assert (
            user_client.get(KEEP_ROUTE.path()).json()["items"][0]["state"]
            == "active"
        )

    def test_decline_attacker(self, init_users, attacker_client, user_client):
        user_client.post(
            KEEP_ROUTE.path(),
            json=RequestKeep(to_id=ADMIN_TOKEN.subject).dict(),
        )
        keep_id = user_client.get(KEEP_ROUTE.path()).json()["items"][0]["id"]

        get_resp = attacker_client.get(KEEP_ROUTE.path()).json()
        assert get_resp["total"] == 0
        resp = attacker_client.put(
            KEEP_ROUTE.concat("decline").path(),
            json=DeclineKeep(keep_id=keep_id, reason="323").dict(),
        )
        assert resp.status_code == 403
        assert (
            user_client.get(KEEP_ROUTE.path()).json()["items"][0]["state"]
            == "pending"
        )

    def test_decline_d(self, init_users, admin_client, user_client, bus):
        user_client.post(
            KEEP_ROUTE.path(),
            json=RequestKeep(to_id=ADMIN_TOKEN.subject).dict(),
        )
        keep_id = user_client.get(KEEP_ROUTE.path()).json()["items"][0]["id"]

        # Decline it by the requested part
        admin_r = admin_client.put(
            KEEP_ROUTE.concat("decline").path(),
            json=DeclineKeep(keep_id=keep_id, reason="something").dict(),
        )
        assert admin_r.status_code == 204
        with bus.uows.get(Keep) as uow:
            keep = uow.repo.get(DomainId(id=keep_id))
            assert keep.state == RootAggState.REMOVED
            assert keep.declined_by == "requested"

    def test_decline_r(self, init_users, user_client, bus):
        user_client.post(
            KEEP_ROUTE.path(),
            json=RequestKeep(to_id=ADMIN_TOKEN.subject).dict(),
        )
        keep_id = user_client.get(KEEP_ROUTE.path()).json()["items"][0]["id"]

        # Decline it by the requested part
        resp = user_client.put(
            KEEP_ROUTE.concat("decline").path(),
            json=DeclineKeep(keep_id=keep_id, reason="something").dict(),
        )
        assert resp.status_code == 204
        with bus.uows.get(Keep) as uow:
            keep = uow.repo.get(DomainId(id=keep_id))
            assert keep.state == RootAggState.REMOVED
            assert keep.declined_by == "requester"

    def test_duplicated(self, init_users, user_client):
        user_client.post(
            KEEP_ROUTE.path(),
            json=RequestKeep(to_id=ADMIN_TOKEN.subject).dict(),
        )
        keep_id = user_client.get(KEEP_ROUTE.path()).json()["items"][0]["id"]

        # Decline it by the requested part
        resp = user_client.post(
            KEEP_ROUTE.path(),
            json=RequestKeep(to_id=ADMIN_TOKEN.subject).dict(),
        )

        assert resp.status_code == 201

    def test_get_only_active_and_pending(
        self, init_users, admin_client, user_client
    ):
        # Given a keep
        user_client.post(
            KEEP_ROUTE.path(),
            json=RequestKeep(to_id=ADMIN_TOKEN.subject).dict(),
        )
        keep_id = user_client.get(KEEP_ROUTE.path()).json()["items"][0]["id"]
        # Declined it by the requested part
        admin_client.put(
            KEEP_ROUTE.concat("decline").path(),
            json=DeclineKeep(keep_id=keep_id, reason="something").dict(),
        )
        assert len(user_client.get(KEEP_ROUTE.path()).json()["items"]) == 0

    @staticmethod
    @pytest.fixture
    def init_keeps(bus):
        with bus.uows.get(Keep) as uow:
            repo: KeepRepository = uow.repo
            repo.put(
                Keep(
                    requester=UserId(USER_TOKEN.subject),
                    requested=UserId(ADMIN_TOKEN.subject),
                    state=RootAggState.PENDING,
                )
            )
            repo.put(
                Keep(
                    requester=UserId("anotherUser"),
                    requested=UserId(USER_TOKEN.subject),
                    state=RootAggState.ACTIVE,
                )
            )
            repo.put(
                Keep(
                    requester=UserId(ADMIN_TOKEN.subject),
                    requested=UserId("anotherUser"),
                    state=RootAggState.REMOVED,
                )
            )
            repo.commit()

    def test_get_all_keeps(self, init_users, init_keeps, admin_client):
        resp = admin_client.get(s.API_V1.concat(s.API_KEEPS).path())

        assert resp.status_code == 200
        assert resp.json()["total"] == 3
