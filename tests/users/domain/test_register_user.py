from typing import Any, Dict

import pytest

from kpm.shared.domain.model import RootAggState
from kpm.users.domain.model import (EmailAlreadyExistsException, User,
                                    UsernameAlreadyExistsException)
from kpm.users.domain.usecase.register_user import RegisterUser, UserRegistered
from tests.users.utils import MemoryUserRepository

DataType = Dict[str, Any]


@pytest.fixture
def valid_data() -> DataType:
    repo = MemoryUserRepository()
    repo.clean_all()  # TODO check why repo is not clean here.
    # It looks like is reusing a cached instance
    yield {
        "username": "me",
        "password": "password",
        "email": "mail@mnail.com",
        "repository": repo,
    }
    repo.clean_all()
    del repo


@pytest.mark.unit
class TestRegisterUser:
    def test_register_user_init(self, valid_data):
        r = RegisterUser(**valid_data)

        assert isinstance(r._entity, User)
        assert r._entity.username == valid_data.get("username")
        assert r._entity.salt
        assert len(r._entity.password_hash) == 60
        assert r._event
        assert isinstance(r._event, UserRegistered)
        assert isinstance(r._event.aggregate, User)
        assert r._event.aggregate.state == RootAggState.PENDING_VALIDATION

    def test_sensitive_information_cleared_from_event(self, valid_data):
        r = RegisterUser(**valid_data)
        assert not r._event.aggregate.password_hash
        assert not r._event.aggregate.salt

    def test_user_is_saved_to_registry(self, valid_data):

        repo = valid_data.get("repository")
        r = RegisterUser(**valid_data)
        r.execute()
        u = r._entity

        assert len(repo.all()) == 1
        assert repo.get(u.id) == u
        assert u.salt
        assert u.password_hash

    def test_email_is_unique(self, valid_data):
        r = RegisterUser(**valid_data)
        r.execute()
        valid_data["username"] = "another_one"
        r2 = RegisterUser(**valid_data)
        with pytest.raises(EmailAlreadyExistsException):
            r2.execute()

    def test_username_is_unique(self, valid_data):
        r = RegisterUser(**valid_data)
        r.execute()
        valid_data["email"] = "another@email.com"
        r2 = RegisterUser(**valid_data)
        with pytest.raises(UsernameAlreadyExistsException):
            r2.execute()

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
    def test_non_allowed_usernames(self, valid_data, wrong_username):
        valid_data["username"] = wrong_username
        with pytest.raises(ValueError):
            RegisterUser(**valid_data)
