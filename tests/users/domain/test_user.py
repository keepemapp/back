import pytest
from typing import Any, Dict

from emo.users.domain.entity.users import User
from emo.shared.domain import UserId, DomainId


DataType = Dict[str, Any]


@pytest.fixture
def valid_data() -> DataType:
    return {
            "id": UserId("as092092"),
            "username": "me",
            "salt": "somesalt",
            "password_hash": "90quh89hhlñhldjqasda==",
            "email": "mail@mnail.com"
        }


@pytest.fixture
def fixture_invalid_userid() -> DataType:
    return {
            "id": "sds",
            "username": "me",
            "salt": "somesalt",
            "password_hash": "90quh89hhlñhldjqasda==",
            "email": "mail@mnail.com"
        }


@pytest.fixture.unit
class TestUser:

    def test_constructor_should_create_instance(self, valid_data):
        u = User(**valid_data)

        assert u.id == valid_data["id"]
        assert u.username == valid_data["username"]
        assert u.salt == valid_data["salt"]
        assert u.password_hash == valid_data["password_hash"]
        assert u.email == valid_data["email"]

    def test_constructor_should_create_active_users(self, valid_data):
        u = User(**valid_data)

        assert u.disabled == False

    def test_id_shall_be_class_userid(self, valid_data):
        valid_data["id"] = 3324
        assert isinstance(UserId("as092092"), DomainId)
        with pytest.raises(ValueError) as e:
            User(**valid_data)

    def test_email_should_be_valid(self, valid_data):
        valid_data["email"] = "asds"
        with pytest.raises(ValueError) as e:
            User(**valid_data)