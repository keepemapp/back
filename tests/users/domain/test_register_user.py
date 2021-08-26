import pytest
from typing import Any, Dict

from tests.utils import TestEventPublisher
from tests.users.utils import MemoryUserRepository
from emo.users.domain.entity.users import User
from emo.users.domain.usecase.register_user import RegisterUser, UserRegistered
from emo.users.domain.usecase.exceptions import EmailAlreadyExistsException, UsernameAlreadyExistsException


DataType = Dict[str, Any]


@pytest.yield_fixture(scope='function')
def valid_data() -> DataType:
    repo = MemoryUserRepository()
    repo.clean_all() # TODO check why repo is not clean here. It looks like is reusing a cached instance
    yield {
        "username": "me",
        "password": "password",
        "email": "mail@mnail.com",
        "repository": repo,
        "message_bus": TestEventPublisher(),
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

    def test_event_is_published(self, valid_data):
        print(valid_data["repository"].all())
        r = RegisterUser(**valid_data)
        r.execute()
        e = r._event
        bus = valid_data.get("message_bus")

        assert bus.published_event == e

    def test_email_is_unique(self, valid_data):
        r = RegisterUser(**valid_data)
        r.execute()
        valid_data['username'] = "another one"
        r2 = RegisterUser(**valid_data)
        with pytest.raises(EmailAlreadyExistsException):
            r2.execute()

    def test_username_is_unique(self, valid_data):
        r = RegisterUser(**valid_data)
        r.execute()
        valid_data['email'] = "another@email.com"
        r2 = RegisterUser(**valid_data)
        with pytest.raises(UsernameAlreadyExistsException):
            r2.execute()
