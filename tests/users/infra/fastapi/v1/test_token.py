import time

import pytest

from kpm.settings import settings as s
from kpm.shared.domain.time_utils import now_utc_sec
from kpm.shared.entrypoints.auth_jwt import from_token
from tests.users.infra.fastapi import client
from tests.users.infra.fastapi.v1.test_users import create_user

user_route: str = s.API_V1.concat(s.API_USER_PATH).prefix
login_route: str = s.API_V1.concat(s.API_TOKEN).prefix


@pytest.mark.unit
class TestJwtTokens:
    user_email: str
    user_id: str
    user_pwd: str

    @pytest.fixture
    def client_with_user(self, client):
        user, response = create_user(client)
        self.user_email = user.email
        self.user_pwd = user.password
        return client

    def test_validity(self, client_with_user):
        time.sleep(1)
        time2 = now_utc_sec()
        response = client_with_user.post(
            login_route,
            data={"username": self.user_email, "password": self.user_pwd},
        )

        assert response.status_code == 200
        assert "refresh_token" in response.json()
        assert "access_token" in response.json()
        time3 = now_utc_sec()

        for tok_type in ["access_token", "refresh_token"]:
            token = from_token(response.json()[tok_type])
            assert token
            assert response.json()[f"{tok_type}_expires"] == token.exp_time
            assert time2 <= token.not_before
            assert token.not_before <= time3
            assert time2 <= token.issued_at
            assert token.issued_at <= time3

    def test_token_refresh(self, client_with_user):
        login_js = client_with_user.post(
            login_route,
            data={"username": self.user_email, "password": self.user_pwd},
        ).json()
        refresh = login_js["refresh_token"]
        r_token = "Bearer " + str(refresh)
        time.sleep(1)
        response = client_with_user.post(
            s.API_V1.concat("/refresh").path(),
            headers={"Accept": "application/json", "Authorization": r_token},
        )
        assert response.status_code == 200
        refresh_js = response.json()

        old_expires = login_js["access_token_expires"]
        new_expires = refresh_js["access_token_expires"]
        assert old_expires < new_expires
