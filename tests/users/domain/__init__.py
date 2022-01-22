import uuid
from typing import Any, Dict

import pytest

from kpm.shared.domain.model import RootAggState, UserId
from kpm.users.domain.model import Keep, User
from tests.users.utils import MemoryUserRepository

DataType = Dict[str, Any]

pwd_group = {
    "plain": "password",
    "salt": "",
    "hash": "$2b$12$Hzgp1lAu1tA5O1Qizcjei.KXMhl9Z5.uejg5RePR9whnDuAqTbCQi",
}


@pytest.fixture
def valid_user() -> DataType:
    yield {
        "id": UserId(str(uuid.uuid4())),
        "username": "me",
        "salt": pwd_group["salt"],
        "password_hash": pwd_group["hash"],
        "email": "mail@mnail.com",
    }


@pytest.fixture
def active_user(valid_user) -> DataType:
    valid_user["state"] = RootAggState.ACTIVE
    yield valid_user


@pytest.fixture
def user(active_user) -> User:
    yield User(**active_user)


@pytest.fixture
def user2(active_user) -> User:
    active_user["id"] = UserId(str(uuid.uuid4()))
    active_user["email"] = "second@email.com"
    active_user["username"] = "iamsecond"
    yield User(**active_user)


@pytest.fixture
def user_repo_with_test_user(active_user) -> MemoryUserRepository:
    repo = MemoryUserRepository()
    repo.create(User(**active_user))
    try:
        yield repo
    finally:
        repo.clean_all()


__all__ = [
    "valid_user",
    "active_user",
    "user_repo_with_test_user",
    "DataType",
    "pwd_group",
    "user",
    "user2",
]
