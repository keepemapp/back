import pytest

from kpm.settings import settings as s
from kpm.shared.domain.model import UserId
from kpm.users.domain.model import User
from kpm.users.domain.repositories import UserRepository
from kpm.users.entrypoints.fastapi.v1.schemas.keeps import (AcceptKeep,
                                                            DeclineKeep,
                                                            RequestKeep)
from tests.users.domain import active_user, valid_user
from tests.users.entrypoints.fastapi import *

KEEP_ROUTE = s.API_V1.concat(s.API_KEEP_PATH)


@pytest.fixture
def init_users(bus, active_user):
    with bus.uows.get(User) as uow:
        repo: UserRepository = uow.repo
        active_user["id"] = UserId(ADMIN_TOKEN.subject)
        active_user["email"] = f"{ADMIN_TOKEN.subject}@email.com"
        repo.create(User(**active_user))

        active_user["id"] = UserId(USER_TOKEN.subject)
        active_user["email"] = f"{USER_TOKEN.subject}@email.com"
        repo.create(User(**active_user))

        uow.commit()
    return True


@pytest.mark.unit
class TestKeepsApi:
    def test_request_keep(self, init_users, admin_client, user_client):
        for client in (user_client, admin_client):
            start_resp = client.get(KEEP_ROUTE.path())
            assert start_resp.status_code == 200
            assert start_resp.json()["total"] == 0

        new_keep = user_client.post(
            KEEP_ROUTE.path(),
            json=RequestKeep(to_user=ADMIN_TOKEN.subject).dict(),
        )
        assert new_keep.status_code == 201

        for client in (user_client, admin_client):
            keep_resp = client.get(KEEP_ROUTE.path())
            assert keep_resp.json()["total"] == 1
            assert keep_resp.json()["items"][0]["state"] == "pending"
            assert (
                ADMIN_TOKEN.subject
                in keep_resp.json()["items"][0]["requested"]
            )
            assert (
                USER_TOKEN.subject in keep_resp.json()["items"][0]["requester"]
            )
            assert keep_resp.json()["items"][0]["id"]

    def test_attacker(self, init_users, user_client, attacker_client):
        user_client.post(
            KEEP_ROUTE.path(),
            json=RequestKeep(to_user=ADMIN_TOKEN.subject).dict(),
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
            json=RequestKeep(to_user=ADMIN_TOKEN.subject).dict(),
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
            json=RequestKeep(to_user=ADMIN_TOKEN.subject).dict(),
        )
        keep_id = user_client.get(KEEP_ROUTE.path()).json()["items"][0]["id"]

        print(user_client)
        print(admin_client)
        print(user_client.get(s.API_V1.concat("me").path()).json())
        print(admin_client.get(s.API_V1.concat("me").path()).json())
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
            json=RequestKeep(to_user=ADMIN_TOKEN.subject).dict(),
        )
        keep_id = user_client.get(KEEP_ROUTE.path()).json()["items"][0]["id"]

        # Finally, accept it
        resp = attacker_client.put(
            KEEP_ROUTE.concat("decline").path(),
            json=DeclineKeep(keep_id=keep_id, reason="323").dict(),
        )
        assert resp.status_code == 403
        assert (
            user_client.get(KEEP_ROUTE.path()).json()["items"][0]["state"]
            == "pending"
        )

    def test_decline_d(self, init_users, admin_client, user_client):
        user_client.post(
            KEEP_ROUTE.path(),
            json=RequestKeep(to_user=ADMIN_TOKEN.subject).dict(),
        )
        keep_id = user_client.get(KEEP_ROUTE.path()).json()["items"][0]["id"]

        # Decline it by the requested part
        admin_r = admin_client.put(
            KEEP_ROUTE.concat("decline").path(),
            json=DeclineKeep(keep_id=keep_id, reason="something").dict(),
        )
        assert admin_r.status_code == 204
        keep = user_client.get(KEEP_ROUTE.path()).json()["items"][0]
        assert keep["state"] == "removed"
        assert keep["declined_by"] == "requested"
        assert "declined_reason" not in keep.keys()

    def test_decline_r(self, init_users, user_client):
        user_client.post(
            KEEP_ROUTE.path(),
            json=RequestKeep(to_user=ADMIN_TOKEN.subject).dict(),
        )
        keep_id = user_client.get(KEEP_ROUTE.path()).json()["items"][0]["id"]

        # Decline it by the requested part
        resp = user_client.put(
            KEEP_ROUTE.concat("decline").path(),
            json=DeclineKeep(keep_id=keep_id, reason="something").dict(),
        )
        assert resp.status_code == 204
        keep = user_client.get(KEEP_ROUTE.path()).json()["items"][0]
        assert keep["state"] == "removed"
        assert keep["declined_by"] == "requester"
        assert "declined_reason" not in keep.keys()
