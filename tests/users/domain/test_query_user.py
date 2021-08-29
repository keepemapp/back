from typing import Any, Dict

import pytest

from emo.shared.domain import UserId
from emo.users.domain.usecase.query_user import QueryUser
from tests.users.domain import user_repo_with_test_user, valid_user
from tests.users.utils import MemoryUserRepository


@pytest.mark.unit
class TestGetUser:
    def test_get_user_id(self, user_repo_with_test_user):
        user = user_repo_with_test_user.all()[0]
        q = QueryUser(repository=user_repo_with_test_user)
        res = q.fetch_by_id(user.id)
        assert res == user

    def test_get_user_email(self, user_repo_with_test_user):
        user = user_repo_with_test_user.all()[0]
        q = QueryUser(repository=user_repo_with_test_user)
        res = q.fetch_by_email(user.email)
        assert res == user

    def test_get_all_users(self, user_repo_with_test_user):
        q = QueryUser(repository=user_repo_with_test_user)
        assert q.fetch_all() == user_repo_with_test_user.all()

    def test_unknown_userid(self, user_repo_with_test_user):
        q = QueryUser(repository=user_repo_with_test_user)
        assert not q.fetch_by_id(UserId('nonexisting'))

    def test_unknown_email(self, user_repo_with_test_user):
        q = QueryUser(repository=user_repo_with_test_user)
        assert not q.fetch_by_email("notanemailatall")

    def test_empty_repository(self, user_repo_with_test_user):
        r = MemoryUserRepository()
        r.clean_all()
        q = QueryUser(repository=r)
        assert not q.fetch_all()
        assert not q.fetch_by_email("notanemailatall")
        assert not q.fetch_by_id(UserId('nonexisting'))