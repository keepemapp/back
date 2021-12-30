import pytest

from kpm.shared.domain import DomainId, IdTypeException
from kpm.shared.domain.model import UserId
from kpm.users.domain.entity.users import User
from tests.users.domain import active_user, valid_user


@pytest.mark.unit
class TestUser:
    class TestModel:
        def test_constructor_should_create_instance(self, active_user):
            u = User(**active_user)

            assert u.id == active_user["id"]
            assert u.username == active_user["username"]
            assert u.salt == active_user["salt"]
            assert u.password_hash == active_user["password_hash"]
            assert u.email == active_user["email"]

        def test_new_user_needs_validation(self, valid_user):
            u = User(**valid_user)
            assert u.is_disabled()
            assert u.is_pending_validation()

        def test_id_shall_be_class_userid(self, active_user):
            active_user["id"] = 3324
            with pytest.raises(IdTypeException) as _:
                User(**active_user)

            active_user["id"] = DomainId("232")
            with pytest.raises(IdTypeException) as _:
                User(**active_user)

            active_user["id"] = UserId("232")
            assert isinstance(User(**active_user).id, UserId)

        def test_email_should_be_valid(self, active_user):
            active_user["email"] = "asds"
            with pytest.raises(ValueError) as _:
                User(**active_user)

    class TestActions:
        def test_user_disable(self, active_user):
            u = User(**active_user)
            assert not u.is_disabled()
            u.disable()
            assert u.is_disabled()
