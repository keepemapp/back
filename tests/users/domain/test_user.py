import pytest

from kpm.shared.domain import DomainId, IdTypeException, UserId
from kpm.users.domain.entity.users import User
from tests.users.domain import valid_user


@pytest.mark.unit
class TestUser:
    class TestModel:
        def test_constructor_should_create_instance(self, valid_user):
            u = User(**valid_user)

            assert u.id == valid_user["id"]
            assert u.username == valid_user["username"]
            assert u.salt == valid_user["salt"]
            assert u.password_hash == valid_user["password_hash"]
            assert u.email == valid_user["email"]

        def test_constructor_should_create_active_users(self, valid_user):
            u = User(**valid_user)
            assert not u.disabled

        def test_id_shall_be_class_userid(self, valid_user):
            valid_user["id"] = 3324
            with pytest.raises(IdTypeException) as _:
                User(**valid_user)

            valid_user["id"] = DomainId("232")
            with pytest.raises(IdTypeException) as _:
                User(**valid_user)

            valid_user["id"] = UserId("232")
            assert isinstance(User(**valid_user).id, UserId)

        def test_email_should_be_valid(self, valid_user):
            valid_user["email"] = "asds"
            with pytest.raises(ValueError) as _:
                User(**valid_user)

    class TestActions:
        def test_user_disable(self, valid_user):
            u = User(**valid_user)
            assert not u.disabled
            disabled_user = u.disable()
            assert disabled_user.disabled
