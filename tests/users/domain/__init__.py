from typing import Any, Dict

import pytest

from kpm.shared.domain import DomainId
from kpm.shared.domain.model import UserId
from kpm.users.domain.entity.users import User
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
        "id": UserId("as092092"),
        "username": "me",
        "salt": pwd_group["salt"],
        "password_hash": pwd_group["hash"],
        "email": "mail@mnail.com",
    }


@pytest.fixture
def user_repo_with_test_user(valid_user) -> MemoryUserRepository:
    repo = MemoryUserRepository()
    repo.create(User(**valid_user))
    try:
        yield repo
    finally:
        repo.clean_all()
