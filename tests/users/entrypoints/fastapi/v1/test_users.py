import pytest

from kpm.settings import settings as s
from kpm.shared.domain.model import RootAggState, UserId
from kpm.users.domain.model import INVALID_USERNAME, User
from kpm.users.domain.repositories import UserRepository
from kpm.users.entrypoints.fastapi.v1.schemas.users import (
    PasswordUpdate,
    Reminder, UserCreate,
    UserRemoval,
    UserUpdate,
)
from tests.users.domain import active_user, valid_user
from tests.users.entrypoints.fastapi import *
from tests.users.fixtures import mongo_client

USER_PATH = s.API_V1.concat(s.API_USER_PATH)
ME_PATH = s.API_V1.concat("/me")
me_route = ME_PATH.path()
user_route: str = USER_PATH.path()
login_route: str = s.API_V1.concat(s.API_TOKEN).prefix
USER_PWD = "THIS_IS_AN_ALLOWED_PASSWORD_LETS_SAY"


def create_direct_user(client, username, email):
    user = UserCreate(username=username, email=email, password=USER_PWD)
    response = client.post(user_route, json=user.dict())
    assert response.status_code == 201
    return user, response


def create_user(client, user_num: int = 0, username=None):
    if not username:
        username = f"user{user_num}"
    return create_direct_user(client, username, f"valid{user_num}@email.com")


def create_active_user(client, user_num: int = 0, username=None):
    # activate_route = USER_PATH.concat(create_resp.json()["id"], "/activate")
    # activ_res = client.put(activate_route.path())
    # assert activ_res.status_code == 201
    return create_user(client, user_num, username)


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

        uow.commit()
    return admin, user


@pytest.mark.unit
class TestRegisterUser:
    def test_create(self, client):
        user = UserCreate(
            username="user", email="valid@email.com", password=USER_PWD
        )
        response = client.post(user_route, json=user.dict())
        assert response.status_code == 201
        user_resp = response.json()
        assert user_resp.get("username") == user.username
        assert user_resp.get("email") == user.email
        assert user_resp.get("id")
        assert user_resp.get("id") in user_resp.get("links").get("self")
        assert user_resp.get("referral_code")

    def test_create_noemail(self, client):
        user = UserCreate(username="user", email="", password=USER_PWD)
        response = client.post(user_route, json=user.dict())
        assert response.status_code == 400
        user_resp = response.json()
        assert user_resp.get("detail") == "Email is not valid"

    def test_referral(self, client):
        _, create_resp = create_user(client)
        referrer_id = create_resp.json().get("id")
        referral_code = create_resp.json().get("referral_code")

        user = UserCreate(
            username="user",
            email="valid@email.com",
            password=USER_PWD,
            referral_code=referral_code,
        )
        response = client.post(user_route, json=user.dict())
        assert response.status_code == 201
        user_resp = response.json()
        assert user_resp.get("referred_by") == referrer_id
        # the created user gets a new referral code different from the original
        assert user_resp.get("referral_code") != referral_code

    def test_no_existant_referral(self, client):
        _, create_resp = create_user(client)
        user = UserCreate(
            username="user2",
            email="valid2@email.com",
            password=USER_PWD,
            referral_code="does not exist",
        )
        response = client.post(user_route, json=user.dict())
        assert response.status_code == 404

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
        assert create_resp.json()["state"] == RootAggState.PENDING.value

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
        user = UserCreate(
            username=wrong_username,
            email="email@correct.com",
            password=USER_PWD,
        )
        response = client.post(user_route, json=user.dict())
        assert response.status_code == 400
        assert response.json().get("detail") == INVALID_USERNAME

    not_allowed_emails = [
        "noemail",
        "noemail@sds",
        "@asdsd.com",
        "de'sdklw@asdsd.com",
        "",
    ]

    @pytest.mark.parametrize("wrong_email", not_allowed_emails)
    def test_wrong_email(self, client, wrong_email):
        user = UserCreate(
            username="user", email=wrong_email, password=USER_PWD
        )
        response = client.post(user_route, json=user.dict())
        assert response.status_code == 400

    not_allowed_passwords = [
        "1234567",
        "",
        "1",
    ]

    @pytest.mark.parametrize("wrong_pwd", not_allowed_passwords)
    def test_invalid_password(self, client, wrong_pwd):
        error_messages = [
            "Password too short. Minimum 8 is characters.",
            "Password too long. Maximum of 96 allowed.",
        ]

        user = UserCreate(
            username="user", email="some@email.com", password=wrong_pwd
        )
        response = client.post(user_route, json=user.dict())
        assert response.status_code == 400
        assert response.json().get("detail") in error_messages

    def test_existing_username(self, client):
        user = UserCreate(
            username="user", email="valid@email.com", password=USER_PWD
        )
        client.post(user_route, json=user.dict())
        user2 = UserCreate(
            username="user", email="valid2@email.com", password=USER_PWD
        )
        response = client.post(user_route, json=user2.dict())
        assert response.status_code == 400
        assert response.json()["detail"]  # We return some error message

    EQUIVALENT_EMAILS = [
        ("valid@gmail.com", "valid@gmail.com"),
        ("valid@gmail.com", "va.lid@gmail.com"),
        ("v.alid@gmail.com", "valid@gmail.com"),
        ("v.alid@gmail.com", "vali.d@gmail.com"),
        ("v.alid@gmail.com", "vali.d@gmail.com"),
        ("  valid@gmail.com", "valid@gmail.com"),
        ("valid@gmail.com  ", "valid@gmail.com"),
        (" valid@gmail.com  ", "valid@gmail.com"),
    ]

    @pytest.mark.parametrize("email_pairs", EQUIVALENT_EMAILS)
    def test_existing_email(self, client, email_pairs):
        user = UserCreate(
            username="user", email=email_pairs[0], password=USER_PWD
        )
        client.post(user_route, json=user.dict())
        user2 = UserCreate(
            username="user2", email=email_pairs[1], password=USER_PWD
        )
        response = client.post(user_route, json=user2.dict())
        assert response.status_code == 400
        assert response.json()["detail"]  # We return some error message

    DIFFERENT_EMAILS = [
        ("valid@hotmail.com", "va.lid@hotmail.com"),
        ("valid@gmail.com", "valid@hotmail.com"),
        ("valid@gmail.com", "val.id@hotmail.com"),
    ]

    @pytest.mark.parametrize("email_pairs", DIFFERENT_EMAILS)
    def test_different_email(self, client, email_pairs):
        user = UserCreate(
            username="user", email=email_pairs[0], password=USER_PWD
        )
        client.post(user_route, json=user.dict())
        user2 = UserCreate(
            username="user2", email=email_pairs[1], password=USER_PWD
        )
        response = client.post(user_route, json=user2.dict())
        assert response.status_code == 201

    def test_create_multiple(self, client):
        for i in range(10):
            user, response = create_active_user(client, i)
            assert response.status_code == 201
            user_resp = response.json()
            assert user_resp.get("username") == user.username
            assert user_resp.get("email") == user.email
            assert user_resp.get("id")
            assert user_resp.get("id") in user_resp.get("links").get("self")


@pytest.mark.unit
class TestGetUsers:
    def test_me_requires_login(self, client):
        response = client.get(me_route)
        assert response.status_code == 401

    def test_token_invalid(self, client):
        user, response = create_active_user(client)
        tok_log = client.post(
            login_route, data={"username": user.email, "password": USER_PWD}
        )

        response = client.get(
            me_route, headers={"Authorization": f"Bearer asd2"}
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

    EQUIVALENT_EMAILS = [
        ("valid@gmail.com", "valid@gmail.com"),
        ("valid@gmail.com", "va.lid@gmail.com"),
        ("v.alid@gmail.com", "valid@gmail.com"),
        ("v.alid@gmail.com", "vali.d@gmail.com"),
        ("v.alid@gmail.com", "vali.d@gmail.com"),
        ("valid@gmail.com", " valid@gmail.com "),
        ("valid@gmail.com", "  valid@gmail.com  "),
    ]

    @pytest.mark.parametrize("email_pairs", EQUIVALENT_EMAILS)
    def test_login_dot_gmail_same_user(self, client, email_pairs):
        create_direct_user(client, "userid", email_pairs[0])

        response = client.post(
            login_route,
            data={"username": email_pairs[0], "password": USER_PWD},
        )
        assert response.status_code == 200

        response = client.post(
            login_route,
            data={"username": email_pairs[1], "password": USER_PWD},
        )
        assert response.status_code == 200

    DIFFERENT_EMAILS = [
        ("valid@hotmail.com", "va.lid@hotmail.com"),
        ("valid@gmail.com", "valid@hotmail.com"),
        ("valid@gmail.com", "val.id@hotmail.com"),
    ]

    @pytest.mark.parametrize("email_pairs", DIFFERENT_EMAILS)
    def test_login_dot_mail_different_users(self, client, email_pairs):
        create_direct_user(client, "userid", email_pairs[0])
        response = client.post(
            login_route,
            data={"username": email_pairs[0], "password": USER_PWD},
        )
        assert response.status_code == 200

        response = client.post(
            login_route,
            data={"username": email_pairs[1], "password": USER_PWD},
        )
        assert response.status_code == 401

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
            me_route,
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
            me_route,
            headers={"Accept": "application/json", "Authorization": token},
        )
        assert response.status_code == 200
        user_resp = response.json()
        assert user_resp == create_resp.json()


@pytest.mark.unit
class TestUserUpdates:
    ATTR_UPDATES = [{"public_name": "new_public_name"}]

    @pytest.mark.parametrize("updates", ATTR_UPDATES)
    def test_update(self, client, user_client, updates):
        user, create_resp = create_active_user(client, 343)
        tok_log = user_client.post(
            login_route,
            data={"username": user.email, "password": user.password},
        )
        token = "Bearer " + str(tok_log.json().get("access_token"))

        response = client.patch(
            ME_PATH.path(),
            json=UserUpdate(**updates).dict(),
            headers={"Accept": "application/json", "Authorization": token},
        )
        print(response.text)
        assert response.status_code == 200

        me = client.get(
            me_route,
            headers={"Accept": "application/json", "Authorization": token},
        ).json()

        for f, v in updates.items():
            assert me[f] == v

    OLD_NEW_PASSWORDS = [
        (USER_PWD, "kasdjkns92mls-klñasd", 200),
        (USER_PWD, "kasd", 400),
        (USER_PWD, "", 400),
        ("", "", 400),
        ("", "thisisagoodpasswordhere23+", 401),
        ("wrong-password", "thisisagoodpasswordhere23+", 401),
    ]

    @pytest.mark.parametrize("passwords", OLD_NEW_PASSWORDS)
    def test_update_password(self, client, passwords):
        user, create_resp = create_active_user(client, 343)
        tok_log = client.post(
            login_route,
            data={"username": user.email, "password": USER_PWD},
        )
        assert tok_log.status_code == 200
        token = "Bearer " + str(tok_log.json().get("access_token"))

        response = client.patch(
            ME_PATH.concat("change-password").path(),
            json=PasswordUpdate(
                old_password=passwords[0], new_password=passwords[1]
            ).dict(),
            headers={"Accept": "application/json", "Authorization": token},
        )
        print(response.text)
        assert response.status_code == passwords[2]

        old_pwd_login_code = 401
        new_pwd_login_code = 2
        if passwords[2] != 200:
            old_pwd_login_code = 200
            new_pwd_login_code = 4

        login_old = client.post(
            login_route,
            data={"username": user.email, "password": USER_PWD},
        )
        assert login_old.status_code == old_pwd_login_code

        login_new = client.post(
            login_route,
            data={"username": user.email, "password": passwords[1]},
        )
        assert login_new.status_code // 100 == new_pwd_login_code

    def test_remove_user_no_exists(self, bus, admin_client):
        user_path = USER_PATH.concat("idonotexist").path()

        # When
        req = admin_client.delete(
            user_path, json=UserRemoval(reason="").dict()
        )

        # Then
        assert req.status_code == 404

    def test_remove_user_requires_reason(self, bus, init_users, admin_client):
        admin, user = init_users
        user_path = USER_PATH.concat(user.id.id).path()

        # When
        req = admin_client.delete(user_path)

        # Then
        assert req.status_code == 422

    def test_remove_user_by_admin(self, bus, init_users, admin_client):
        admin, user = init_users
        user_path = USER_PATH.concat(user.id.id).path()

        # When
        req = admin_client.delete(
            user_path, json=UserRemoval(reason="").dict()
        )

        # Then
        assert req.status_code == 200

        with bus.uows.get(User) as uow:
            repo: UserRepository = uow.repo
            u = repo.get(user.id)
            assert u.state == RootAggState.REMOVED
            assert not u.public_name
            assert u.email != user.email

    def test_remove_user_by_user(self, init_users, user_client):
        admin, user = init_users
        user_path = USER_PATH.concat(user.id.id).path()

        req = user_client.delete(user_path, json=UserRemoval(reason="").dict())
        assert req.status_code == 403

    def test_add_reminder(self, init_users, user_client):
        admin, user = init_users
        user_path = USER_PATH.concat("me", "reminders").path()
        # When
        result = user_client.post(
            user_path,
            json=[Reminder(title="r1", time=1234).dict()],
        )
        # Then
        assert result.status_code == 201

    def test_add_duplicated_reminders(self, init_users, user_client):
        admin, user = init_users
        user_path = USER_PATH.concat("me", "reminders").path()
        initial = [Reminder(title="r1", time=1234).dict(),
                   Reminder(title="r2", time=1234).dict(),
                   Reminder(title="r3", time=1234).dict()]
        update = [Reminder(title="r1", time=1234).dict(),
                  Reminder(title="r2", time=1234, related_user=admin.id.id).dict(),
                  Reminder(title="r3", time=1234, frequency=1223).dict(),
                  Reminder(title="r4", time=122, frequency=23).dict()]
        user_client.post(user_path, json=initial)

        # When
        result = user_client.post(user_path, json=update)
        # Then
        assert result.status_code == 201
        reminders = user_client.get(user_path).json()
        assert len(reminders) == 4
        print(reminders)
        for resp in reminders:
            assert resp in update

    def test_get_reminders(self, init_users, user_client):
        # Given
        admin, user = init_users
        user_path = USER_PATH.concat("me", "reminders").path()
        user_client.post(
            user_path,
            json=[Reminder(title="r1", time=1234).dict()],
        )
        # When
        result = user_client.get(user_path)
        # Then
        assert result.status_code == 200
        results = result.json()
        assert len(results) == 1
        assert results[0] == Reminder(title="r1", time=1234).dict()

    def test_delete_reminders(self, init_users, user_client):
        # Given
        admin, user = init_users
        user_path = USER_PATH.concat("me", "reminders").path()
        user_client.post(
            user_path,
            json=[Reminder(title="r1", time=1234).dict()],
        )
        # When
        result = user_client.delete(
            user_path,
            json=[Reminder(title="r1", time=1234).dict()]
        )
        # Then
        assert result.status_code == 200