from fastapi.security import OAuth2PasswordRequestForm

from emo.settings import settings as s
from emo.users.infrastructure.fastapi.v1.schemas.users import UserCreate
from tests.users.infrastructure.fastapi import get_client

client = get_client()

user_route: str = s.API_V1.concat(s.API_USER_PATH).prefix
login_route: str = s.API_V1.concat(s.API_TOKEN).prefix
USER_PWD = "pwd"


def create_user(user_num: int = 0):
    user = UserCreate(
        username=f"user{user_num}",
        email=f"valid{user_num}@email.com",
        password=USER_PWD,
    )
    response = client.post(user_route, json=user.dict())
    return user, response


class TestRegisterUser:
    def test_create(self):
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

    def test_wrong_email(self):
        user = UserCreate(username="user", email="noemail", password="pwd")
        response = client.post(user_route, json=user.dict())
        assert response.status_code == 400

    def test_existing_username(self):
        user = UserCreate(
            username="user", email="valid@email.com", password="pwd"
        )
        client.post(user_route, json=user.dict())
        user2 = UserCreate(
            username="user", email="valid2@email.com", password="pwd"
        )
        response = client.post(user_route, json=user2.dict())
        assert response.status_code == 400

    def test_existing_email(self):
        user = UserCreate(
            username="user", email="valid@email.com", password="pwd"
        )
        client.post(user_route, json=user.dict())
        user2 = UserCreate(
            username="user2", email="valid@email.com", password="pwd"
        )
        response = client.post(user_route, json=user2.dict())
        assert response.status_code == 400

    def test_create_multiple(self):
        for i in range(10):
            user, response = create_user(i)
            assert response.status_code == 200
            user_resp = response.json()
            assert user_resp.get("username") == user.username
            assert user_resp.get("email") == user.email
            assert user_resp.get("id")
            assert user_resp.get("id") in user_resp.get("links").get("self")


class TestGetUsers:
    def test_me_requires_login(self):
        response = client.get(user_route + "/me")
        assert response.status_code == 401

    def test_token_invalid(self):
        user, response = create_user()
        tok_log = client.post(
            login_route, data={"username": user.email, "password": USER_PWD}
        )
        token = tok_log.json().get("access_token")
        response = client.get(
            user_route + "/me", headers={"Authorization": f"Bearer asd2"}
        )
        assert response.json() == {"detail": "Could not validate credentials"}
        assert response.status_code == 401

    def test_login(self):
        user, response = create_user()
        response = client.post(
            login_route, data={"username": user.email, "password": USER_PWD}
        )
        assert response.status_code == 200
        assert response.json().get("token_type") == "bearer"

    def test_login_username_invalid(self):
        user, _ = create_user()
        response = client.post(
            login_route,
            data={"username": "wrong username", "password": USER_PWD},
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Incorrect username or password"}

    def test_login_password_invalid(self):
        user, _ = create_user()
        response = client.post(
            login_route, data={"username": user.email, "password": "wrong pwd"}
        )
        assert response.status_code == 401
        assert response.json() == {"detail": "Incorrect username or password"}

    def test_token_validity(self):
        user, _ = create_user()
        tok_log = client.post(
            login_route, data={"username": user.email, "password": USER_PWD}
        )
        token = "Bearer " + str(tok_log.json().get("access_token"))

        response = client.get(
            user_route + "/me",
            headers={"Accept": "application/json", "Authorization": token},
        )
        assert response.status_code == 200

    def test_me_returns_user(self):
        user, create_resp = create_user(343)
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
