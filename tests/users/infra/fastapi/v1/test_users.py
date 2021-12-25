import pytest

from kpm.settings import settings as s
from kpm.shared.domain.model import RootAggState
from kpm.users.domain.entity.users import INVALID_USERNAME
from kpm.users.infra.fastapi.v1.schemas.users import UserCreate
from tests.users.infra.fastapi import client

USER_PATH = s.API_V1.concat(s.API_USER_PATH)
user_route: str = USER_PATH.path()
login_route: str = s.API_V1.concat(s.API_TOKEN).prefix
USER_PWD = "pwd"


def create_user(client, user_num: int = 0):
    user = UserCreate(
        username=f"user{user_num}",
        email=f"valid{user_num}@email.com",
        password=USER_PWD,
    )
    response = client.post(user_route, json=user.dict())
    assert response.status_code == 200

    return user, response


def create_active_user(client, user_num: int = 0):
    user, create_resp = create_user(client, user_num)
    # activate_route = USER_PATH.concat(create_resp.json()["id"], "/activate")
    # activ_res = client.put(activate_route.path())
    # assert activ_res.status_code == 200
    return user, create_resp


@pytest.mark.unit
class TestRegisterUser:
    def test_create(self, client):
        user = UserCreate(
            username="user", email="valid@email.com", password="pwd"
        )
        response = client.post(user_route, json=user.dict())
        assert response.status_code == 200
        user_resp = response.json()
        assert user_resp.get("username") == user.username
        assert user_resp.get("email") == user.email
        assert user_resp.get("id")
        assert user_resp.get("id") in user_resp.get("links").get("self")

    def test_first_user_is_admin(self, client):
        _, create_resp = create_user(client)
        assert "roles" in create_resp.json()
        assert "admin" in create_resp.json()["roles"]

    def test_first_user_is_active(self, client):
        _, create_resp = create_user(client)
        assert "state" in create_resp.json()
        assert create_resp.json()["state"] == RootAggState.ACTIVE.value

    def test_second_user(self, client):
        _, create_resp = create_user(client, 1)
        _, create_resp = create_user(client, 2)

        assert "admin" not in create_resp.json()["roles"]
        assert "user" in create_resp.json()["roles"]
        assert (
            create_resp.json()["state"]
            == RootAggState.PENDING_VALIDATION.value
        )

    non_allowed_usernames = [
        "",
        ".a2c",
        "c/sc",
        "78k2_'3",
        "s",
        "#2sd",
        "so 2s",
    ]

    @pytest.mark.parametrize("wrong_username", non_allowed_usernames)
    def test_non_allowed_usernames(self, client, wrong_username):
        # TODO since this has been moved to the use case layer, perhaps
        # simplify me.
        user = UserCreate(
            username=wrong_username, email="email@correct.com", password="pwd"
        )
        response = client.post(user_route, json=user.dict())
        assert response.status_code == 400
        assert response.json().get("detail") == INVALID_USERNAME

    def test_wrong_email(self, client):
        user = UserCreate(username="user", email="noemail", password="pwd")
        response = client.post(user_route, json=user.dict())
        assert response.status_code == 400

    def test_existing_username(self, client):
        user = UserCreate(
            username="user", email="valid@email.com", password="pwd"
        )
        client.post(user_route, json=user.dict())
        user2 = UserCreate(
            username="user", email="valid2@email.com", password="pwd"
        )
        response = client.post(user_route, json=user2.dict())
        assert response.status_code == 400

    def test_existing_email(self, client):
        user = UserCreate(
            username="user", email="valid@email.com", password="pwd"
        )
        client.post(user_route, json=user.dict())
        user2 = UserCreate(
            username="user2", email="valid@email.com", password="pwd"
        )
        response = client.post(user_route, json=user2.dict())
        assert response.status_code == 400

    def test_create_multiple(self, client):
        for i in range(10):
            user, response = create_active_user(client, i)
            assert response.status_code == 200
            user_resp = response.json()
            assert user_resp.get("username") == user.username
            assert user_resp.get("email") == user.email
            assert user_resp.get("id")
            assert user_resp.get("id") in user_resp.get("links").get("self")


@pytest.mark.unit
class TestGetUsers:
    def test_me_requires_login(self, client):
        response = client.get(user_route + "/me")
        assert response.status_code == 401

    def test_token_invalid(self, client):
        user, response = create_active_user(client)
        tok_log = client.post(
            login_route, data={"username": user.email, "password": USER_PWD}
        )

        response = client.get(
            user_route + "/me", headers={"Authorization": f"Bearer asd2"}
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Could not validate credentials"}

    def test_login(self, client):
        user, create_resp = create_active_user(client)
        response = client.post(
            login_route, data={"username": user.email, "password": USER_PWD}
        )
        assert response.status_code == 200
        assert response.json().get("user_id") == create_resp.json().get("id")
        assert "refresh_token" in response.json()
        assert "access_token" in response.json()

    def test_successful_login_returns_user_id(self, client):
        user, resp1 = create_active_user(client)
        user_id = resp1.json().get("id", "no user id provided")
        response = client.post(
            login_route, data={"username": user.email, "password": USER_PWD}
        )
        assert response.status_code == 200
        assert response.json().get("user_id") == user_id

    def test_login_username_invalid(self, client):
        user, _ = create_active_user(client)
        response = client.post(
            login_route,
            data={"username": "wrong username", "password": USER_PWD},
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Incorrect username or password"}

    def test_login_password_invalid(self, client):
        user, _ = create_active_user(client)
        response = client.post(
            login_route, data={"username": user.email, "password": "wrong pwd"}
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Incorrect username or password"}

    def test_token_validity(self, client):
        user, _ = create_active_user(client)
        tok_log = client.post(
            login_route, data={"username": user.email, "password": USER_PWD}
        )
        token = "Bearer " + str(tok_log.json().get("access_token"))

        response = client.get(
            user_route + "/me",
            headers={"Accept": "application/json", "Authorization": token},
        )
        assert response.status_code == 200

    def test_me_returns_user(self, client):
        user, create_resp = create_active_user(client, 343)
        tok_log = client.post(
            login_route, data={"username": user.email, "password": USER_PWD}
        )
        token = "Bearer " + str(tok_log.json().get("access_token"))

        response = client.get(
            user_route + "/me",
            headers={"Accept": "application/json", "Authorization": token},
        )
        assert response.status_code == 200
        user_resp = response.json()
        assert user_resp == create_resp.json()
