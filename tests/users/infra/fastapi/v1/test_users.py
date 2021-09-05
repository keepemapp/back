import pytest

from emo.settings import settings as s
from emo.users.domain.entity.users import INVALID_USERNAME
from emo.users.infra.fastapi.v1.schemas.users import UserCreate
from tests.users.infra.fastapi import client

user_route: str = s.API_V1.concat(s.API_USER_PATH).prefix
login_route: str = s.API_V1.concat(s.API_TOKEN).prefix
USER_PWD = "pwd"


def create_user(client, user_num: int = 0):
    user = UserCreate(
        username=f"user{user_num}",
        email=f"valid{user_num}@email.com",
        password=USER_PWD,
    )
    response = client.post(user_route, json=user.dict())
    return user, response


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
            user, response = create_user(client, i)
            assert response.status_code == 200
            user_resp = response.json()
            assert user_resp.get("username") == user.username
            assert user_resp.get("email") == user.email
            assert user_resp.get("id")
            assert user_resp.get("id") in user_resp.get("links").get("self")


class TestGetUsers:
    def test_me_requires_login(self, client):
        response = client.get(user_route + "/me")
        assert response.status_code == 401

    def test_token_invalid(self, client):
        user, response = create_user(client)
        tok_log = client.post(
            login_route, data={"username": user.email, "password": USER_PWD}
        )
        token = tok_log.json().get("access_token")
        response = client.get(
            user_route + "/me", headers={"Authorization": f"Bearer asd2"}
        )
        assert response.json() == {"detail": "Could not validate credentials"}
        assert response.status_code == 401

    def test_login(self, client):
        user, response = create_user(client)
        response = client.post(
            login_route, data={"username": user.email, "password": USER_PWD}
        )
        assert response.status_code == 200
        assert response.json().get("token_type") == "bearer"

    def test_login_username_invalid(self, client):
        user, _ = create_user(client)
        response = client.post(
            login_route,
            data={"username": "wrong username", "password": USER_PWD},
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Incorrect username or password"}

    def test_login_password_invalid(self, client):
        user, _ = create_user(client)
        response = client.post(
            login_route, data={"username": user.email, "password": "wrong pwd"}
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Incorrect username or password"}

    def test_token_validity(self, client):
        user, _ = create_user(client)
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
        user, create_resp = create_user(client, 343)
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
