import pytest

from kpm.shared.security import salt_password, verify_password
from kpm.users.domain.model import MissmatchPasswordException, User
from kpm.users.domain.usecase.change_user_password import (ChangeUserPassword,
                                                           UserPasswordChanged)
from tests.users.domain import *


@pytest.fixture
def valid_pwd_change(user_repo_with_test_user) -> DataType:
    u = user_repo_with_test_user.all()[0]

    yield {
        "user_id": u.id,
        "old_password": pwd_group["plain"],
        "new_password": "newPassword",
        "repository": user_repo_with_test_user,
    }


@pytest.mark.unit
class TestChangePassword:
    def test_init_change_password(self, valid_pwd_change):
        cp = ChangeUserPassword(**valid_pwd_change)
        assert isinstance(cp._event, UserPasswordChanged)

    def test_new_password_saved(self, valid_pwd_change):
        cp = ChangeUserPassword(**valid_pwd_change)
        cp.execute()

        updated: User = cp._repository.all()[0]
        assert verify_password(
            salt_password(valid_pwd_change["new_password"], updated.salt),
            updated.password_hash,
        )

    def test_fail_old_pw_mismatch(self, valid_pwd_change):
        valid_pwd_change["old_password"] = "Wrong password"
        cp = ChangeUserPassword(**valid_pwd_change)
        with pytest.raises(MissmatchPasswordException) as _:
            cp.execute()

    def test_event_domain_has_no_information(self, valid_pwd_change):
        cp = ChangeUserPassword(**valid_pwd_change)
        uid = cp._repository.all()[0].id
        assert cp._event.aggregate_id == uid
