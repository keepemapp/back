import random
import string
import time
import uuid
from dataclasses import fields

import pytest
from pymongo import MongoClient

from kpm.shared.domain.model import RootAggregate, RootAggState, UserId
from kpm.shared.domain.time_utils import now_utc_millis
from kpm.users.adapters.mongo.repository import KeepMongoRepo, UserMongoRepo
from kpm.users.domain.model import Keep
from tests.users.domain import *


@pytest.fixture
def mongo_client():
    url = "mongodb://127.0.0.1:27017/?replicaSet=rs0"
    yield MongoClient(url)


def assert_result_equality(result: RootAggregate, original: RootAggregate):
    assert isinstance(result, type(original))
    original.events = []
    fs = fields(original)
    for f in fs:
        assert getattr(result, f.name) == getattr(original, f.name)


@pytest.mark.integration
class TestMongoUserRepo:
    @pytest.fixture
    def _repo(self) -> UserMongoRepo:
        url = "mongodb://127.0.0.1:27017/?replicaSet=rs0"
        db = "users_" + "".join(
            random.choice("smiwysndkajsown") for _ in range(5)
        )
        repo = UserMongoRepo(mongo_url=url, mongo_db=db)
        yield db, repo
        repo.rollback()
        client = MongoClient(url)
        client.drop_database(db)

    def test_create(self, _repo, user, mongo_client):
        db, repo = _repo
        repo.create(user)

        collection = mongo_client[db]["users"]
        assert collection.count_documents({}) == 0
        # If no commit

        repo.commit()
        assert collection.count_documents({}) == 1
        a = collection.find_one({"_id": user.id.id})
        assert a["_id"] == user.id.id

    def test_update(self, _repo, user, mongo_client):
        old_name = "old public name"
        new_name = "I am Your cat"

        db, repo = _repo
        user.public_name = old_name
        repo.create(user)
        repo.commit()

        collection = mongo_client[db]["users"]

        # When
        user.update_fields(now_utc_millis(), {"public_name": new_name})
        repo.update(user)
        # Before commit
        a = collection.find_one({"_id": user.id.id})
        assert a["public_name"] == old_name

        repo.commit()
        a = collection.find_one({"_id": user.id.id})
        assert a["public_name"] == new_name

    def test_username_exists(self, _repo, user):
        db, repo = _repo
        repo.create(user)
        repo.commit()

        assert repo.exists_username(user.username)
        for uname in ["asdasd", "notexist", "", "_ad2"]:
            assert not repo.exists_username(uname)

    EQUIVALENT_EMAILS = [
        ("valid@gmail.com", "valid@gmail.com"),
        ("valid@gmail.com", "va.lid@gmail.com"),
        ("v.alid@gmail.com", "valid@gmail.com"),
        ("v.alid@gmail.com", "vali.d@gmail.com"),
        ("v.alid@gmail.com", "vali.d@gmail.com"),
        ("valid@mail.com", "valid@mail.com"),
    ]

    @pytest.mark.parametrize("email_pairs", EQUIVALENT_EMAILS)
    def test_email_exists(self, _repo, user, email_pairs):
        db, repo = _repo
        user.email = email_pairs[0]
        repo.create(user)
        repo.commit()

        assert repo.exists_email(email_pairs[1])

    DIFFERENT_EMAILS = [
        ("valid@hotmail.com", "va.lid@hotmail.com"),
        ("valid@gmail.com", "valid@hotmail.com"),
        ("valid@gmail.com", "val.id@hotmail.com"),
    ]

    @pytest.mark.parametrize("email_pairs", DIFFERENT_EMAILS)
    def test_email_not_exists(self, _repo, user, email_pairs):
        db, repo = _repo
        user.email = email_pairs[0]
        repo.create(user)
        repo.commit()

        assert not repo.exists_email(email_pairs[1])

    def test_get(self, _repo, user, user2):
        db, repo = _repo
        repo.create(user)
        repo.create(user2)
        repo.commit()

        assert_result_equality(repo.get(user.id), user)
        assert_result_equality(repo.get(user2.id), user2)

    def test_all(self, _repo, user, user2):
        db, repo = _repo
        repo.create(user)
        repo.create(user2)
        repo.commit()

        assert len(repo.all()) == 2


@pytest.mark.integration
class TestMongoKeepRepo:
    @pytest.fixture
    def _repo(self) -> KeepMongoRepo:
        url = "mongodb://127.0.0.1:27017/?replicaSet=rs0"
        db = "users_" + "".join(
            random.choice("smiwysndkajsown") for _ in range(5)
        )
        repo = KeepMongoRepo(mongo_url=url, mongo_db=db)
        yield db, repo
        repo.rollback()
        client = MongoClient(url)
        client.drop_database(db)

    def test_create(self, _repo, mongo_client):
        db, repo = _repo
        k = Keep(requester=UserId(id="user1"), requested=UserId(id="user2"))
        repo.put(k)

        collection = mongo_client[db]["keeps"]
        assert collection.count_documents({}) == 0
        # If no commit

        repo.commit()
        assert collection.count_documents({}) == 1
        a = collection.find_one({"_id": k.id.id})
        assert a["_id"] == k.id.id

    def test_update(self, _repo, mongo_client):
        k = Keep(requester=UserId(id="user1"), requested=UserId(id="user2"))
        db, repo = _repo
        repo.put(k)
        repo.commit()
        collection = mongo_client[db]["keeps"]

        # When
        k.accept()
        repo.put(k)
        # Before commit
        a = collection.find_one({"_id": k.id.id})
        assert a["state"] == RootAggState.PENDING.value

        repo.commit()
        a = collection.find_one({"_id": k.id.id})
        assert a["state"] == RootAggState.ACTIVE.value

    @pytest.mark.parametrize("state", [
        RootAggState.ACTIVE,
        RootAggState.PENDING,
        RootAggState.REMOVED,
        RootAggState.INACTIVE,
    ])
    def test_exists(self, _repo, state):
        u1 = UserId(id="user1")
        u2 = UserId(id="user2")
        k = Keep(requester=u1, requested=u2, state=state)
        db, repo = _repo
        repo.put(k)
        repo.commit()

        # Matching
        assert repo.exists(u1, u2, all_states=True)
        assert repo.exists(u2, u1, all_states=True)
        # Self relationship exists and is good
        assert repo.exists(u1, u1, all_states=True)
        assert repo.exists(u1, u1, all_states=False)
        if state == RootAggState.ACTIVE:
            assert repo.exists(u1, u2, all_states=False)
            assert repo.exists(u2, u1, all_states=False)
        else:
            assert not repo.exists(u1, u2, all_states=False)
            assert not repo.exists(u2, u1, all_states=False)

        # Not matching
        assert not repo.exists(UserId(id="34123"), UserId(id="11111"), all_states=True)
        for u in [u1, u2]:
            assert not repo.exists(u, UserId(id="another"), all_states=True)
            assert not repo.exists(UserId(id="another"), u, all_states=True)

    def test_get(self, _repo):
        k = Keep(requester=UserId(id="user1"), requested=UserId(id="user2"))
        db, repo = _repo
        repo.put(k)
        repo.commit()

        assert_result_equality(repo.get(k.id), k)

    def test_all(self, _repo):
        k1 = Keep(requester=UserId(id="user1"), requested=UserId(id="user2"))
        k2 = Keep(requester=UserId(id="user1"), requested=UserId(id="user3"))
        k3 = Keep(requester=UserId(id="user2"), requested=UserId(id="user3"))
        db, repo = _repo
        repo.put(k1)
        repo.put(k2)
        repo.put(k3)
        repo.commit()

        assert len(repo.all()) == 3
