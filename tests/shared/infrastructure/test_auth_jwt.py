import pytest

from kpm.shared.infra.auth_jwt import *


@pytest.mark.unit
class TestJWTToken:
    def test_access_token_creation(self):
        t = AccessToken(subject="user123")
        assert t.exp_time > t.issued_at
        assert t.is_access()
        assert t.scopes == []
        assert t.is_fresh()
        assert t.is_valid()

        t = AccessToken(subject="user123", scopes=["admin"])
        assert t.scopes == ["admin"]

    def test_token_validity(self):
        with pytest.raises(ValueError):
            AccessToken(subject="")
        with pytest.raises(ValueError):
            AccessToken(subject=None)
        with pytest.raises(ValueError):
            AccessToken(subject=3)

        t_admin = AccessToken(
            subject="user123",
            scopes=["admin"],
            exp_time_delta=timedelta(minutes=20),
        )

        assert t_admin.is_valid()
        assert t_admin.is_valid(scope="admin")
        assert not t_admin.is_valid(scope="AnotherScope")

        nbf = int(datetime(2000, 1, 1, 0, 0).timestamp())
        t_old = AccessToken(
            subject="1", not_before=nbf, exp_time_delta=timedelta(seconds=1)
        )
        assert not t_old.is_valid()

        nbf = int(datetime(2222, 1, 1, 0, 0).timestamp())
        t_fture = AccessToken(subject="1", not_before=nbf)
        assert not t_fture.is_valid()

    def test_access_token_freshness(self):
        t = AccessToken(subject="user123")
        assert t.is_fresh()

        t2 = AccessToken(subject="user123", fresh=False)
        assert not t2.is_fresh()

    def test_can_decode_access_token(self):
        t = AccessToken(subject="user123")
        res = from_token(t.to_token())

        assert isinstance(res, AccessToken)
        assert res.jwt_id == t.jwt_id
        assert res.issued_at == t.issued_at
        assert res.not_before == t.not_before
        assert res.subject == t.subject
        assert res.fresh == t.fresh
        assert res.exp_time == t.exp_time
        assert res.scopes == t.scopes
        assert not res.can_generate_str

    def test_creates_refresh_token(self):
        t = RefreshToken(subject="user123")
        assert t.is_refresh()

    def test_can_decode_refresh_token(self):
        t = RefreshToken(subject="user123")

        assert t.exp_time > t.issued_at
        res = from_token(t.to_token())

        assert isinstance(res, RefreshToken)
        assert res.jwt_id == t.jwt_id
        assert res.issued_at == t.issued_at
        assert res.not_before == t.not_before
        assert res.subject == t.subject
        assert res.exp_time == t.exp_time
        assert res.scopes == t.scopes
        assert not res.can_generate_str
