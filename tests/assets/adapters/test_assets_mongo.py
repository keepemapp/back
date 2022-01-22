import random
import string
import time
import uuid
from dataclasses import fields

import pytest
from pymongo import MongoClient

from kpm.assets.adapters.mongo.repository import (
    AssetMongoRepo,
    AssetReleaseMongoRepo,
)
from kpm.assets.domain import DuplicatedAssetException
from kpm.shared.domain.model import (
    AssetId,
    RootAggregate,
    RootAggState,
    UserId,
)
from tests.assets.domain import *


@pytest.fixture
def mongo_client():
    url = "mongodb://127.0.0.1:27017/?replicaSet=rs0"
    yield MongoClient(url)


@pytest.fixture
def assets_repo():
    url = "mongodb://127.0.0.1:27017/?replicaSet=rs0"
    db = "assets_" + "".join(
        random.choice("smiwysndkajsown") for _ in range(5)
    )
    repo = AssetMongoRepo(mongo_url=url, mongo_db=db)
    yield db, repo
    repo.rollback()
    client = MongoClient(url)
    client.drop_database(db)


def assert_result_equality(result: RootAggregate, original: RootAggregate):
    assert isinstance(result, type(original))
    original.events = []
    fs = fields(original)
    for f in fs:
        assert getattr(result, f.name) == getattr(original, f.name)


@pytest.mark.integration
class TestMongoAssetRepo:
    def test_create_asset(self, assets_repo, asset, mongo_client):
        db, repo = assets_repo
        repo.create(asset)

        assets = mongo_client[db]["assets"]
        assert assets.count_documents({}) == 0
        # If no commit

        repo.commit()
        assert assets.count_documents({}) == 1
        a = assets.find_one({"_id": asset.id.id})
        assert a["_id"] == asset.id.id

    def test_cannot_create_duplicate(self, assets_repo, asset, mongo_client):
        db, repo = assets_repo
        repo.create(asset)
        repo.commit()

        with pytest.raises(DuplicatedAssetException):
            repo.create(asset)

        # Then
        assets = mongo_client[db]["assets"]
        assert assets.count_documents({}) == 1

    def test_updates_work(self, assets_repo, asset, mongo_client):
        db, repo = assets_repo
        repo.create(asset)
        repo.commit()

        old_owner = asset.owners_id[0]
        new_owner = UserId(id=str(uuid.uuid4()))

        asset.change_owner(None, old_owner, [new_owner])
        repo.update(asset)

        assets = mongo_client[db]["assets"]
        assert assets.count_documents({"owners_id": old_owner.id}) == 1
        assert assets.count_documents({"owners_id": new_owner.id}) == 0
        # after commit
        repo.commit()

        # Then
        assert assets.count_documents({"owners_id": old_owner.id}) == 0
        assert assets.count_documents({"owners_id": new_owner.id}) == 1

    def test_can_find_by_id(self, assets_repo, asset):
        db, repo = assets_repo
        repo.create(asset)
        repo.commit()

        resp = repo.find_by_id(asset.id)
        assert len(resp.events) == 0
        assert resp.id == asset.id

        # Multiple ids
        results = repo.find_by_ids([asset.id])
        assert len(results) == 1
        a_res = results[0]
        assert isinstance(a_res.file, type(asset.file))
        assert_result_equality(a_res, asset)

    def test_non_existent_asset_id(self, assets_repo, asset):
        db, repo = assets_repo
        repo.create(asset)
        repo.commit()

        resp = repo.find_by_id(AssetId(str(uuid.uuid4())))
        assert not resp

        # Multiple ids
        assert len(repo.find_by_ids([AssetId(str(uuid.uuid4()))])) == 0

    def test_can_find_by_owner(self, assets_repo, asset):
        db, repo = assets_repo
        repo.create(asset)
        repo.commit()

        resps = repo.find_by_ownerid(asset.owners_id[0])
        assert len(resps) == 1
        assert resps[0].id == asset.id

        notmatching = repo.find_by_ownerid(UserId("Random user"))
        assert len(notmatching) == 0

    def test_only_visible(self, assets_repo, asset):
        db, repo = assets_repo
        asset.hide(None)
        repo.create(asset)
        repo.commit()

        assert len(repo.all(visible_only=True)) == 0
        assert len(repo.all(visible_only=False)) == 1

    def test_bookmarked(self, assets_repo, asset, asset2):
        db, repo = assets_repo
        repo.create(asset)
        asset2.bookmarked = True
        repo.create(asset2)
        repo.commit()

        assert len(repo.all()) == 2
        assert len(repo.all(bookmarked=True)) == 1
        assert repo.all(bookmarked=True)[0].id == asset2.id
        assert len(repo.all(bookmarked=False)) == 1
        assert repo.all(bookmarked=False)[0].id == asset.id

    def test_asset_type(self, assets_repo, asset):
        db, repo = assets_repo
        repo.create(asset)
        repo.commit()

        assert len(repo.all(asset_types=[asset.file.type, "anothertype"])) == 1
        assert len(repo.all(asset_types=["anothertype"])) == 0

    def test_order(self, assets_repo, asset, asset2):
        db, repo = assets_repo
        repo.create(asset)
        asset2.created_ts = 10
        repo.create(asset2)
        repo.commit()

        asc = repo.all(order_by="created_ts", order="asc")
        desc = repo.all(order_by="created_ts", order="desc")

        for a1, a2 in zip(asc, [asset2, asset]):
            assert a1.id == a2.id

        for a1, a2 in zip(desc, [asset, asset2]):
            assert a1.id == a2.id

    def test_delete(self, assets_repo, asset, asset2):
        db, repo = assets_repo
        repo.create(asset)
        repo.create(asset2)
        repo.commit()
        assert len(repo.all()) == 2

        repo.remove(asset.id)
        assert len(repo.all()) == 2
        repo.commit()
        assert len(repo.all()) == 1

    def test_delete_non_existent_id(self, assets_repo, asset, asset2):
        # Non existent asset id does not fail
        _, repo = assets_repo
        repo.remove(AssetId(str(uuid.uuid4())))
        repo.commit()
        assert len(repo.all()) == 0

    def test_rollback(self, assets_repo, asset, asset2):
        db, repo = assets_repo
        repo.create(asset)
        repo.rollback()
        assert len(repo.all()) == 0
        repo.create(asset2)
        repo.commit()
        assert len(repo.all()) == 1

    def test_rollback_empty(self, assets_repo):
        db, repo = assets_repo
        repo.rollback()
        assert len(repo.all()) == 0

    def test_commit_empty(self, assets_repo):
        db, repo = assets_repo
        repo.commit()
        assert len(repo.all()) == 0


@pytest.mark.integration
class TestMongoAssetReleaseRepo:
    @pytest.fixture
    def arrepo(self) -> AssetReleaseMongoRepo:
        url = "mongodb://127.0.0.1:27017/?replicaSet=rs0"
        db = "assets_" + "".join(
            random.choice("smiwysndkajsown") for _ in range(5)
        )
        repo = AssetReleaseMongoRepo(mongo_url=url, mongo_db=db)
        yield db, repo
        client = MongoClient(url)
        client.drop_database(db)

    def test_create(self, arrepo, release1, mongo_client):
        db, repo = arrepo
        repo.put(release1)

        collection = mongo_client[db]["releases"]
        assert collection.count_documents({}) == 0
        # If no commit

        repo.commit()
        assert collection.count_documents({}) == 1
        a = collection.find_one({"_id": release1.id.id})
        assert a["_id"] == release1.id.id

    def test_update(self, arrepo, release1, mongo_client):
        db, repo = arrepo
        repo.put(release1)
        repo.commit()

        collection = mongo_client[db]["releases"]
        assert collection.count_documents({}) == 1

        release1.remove(mod_ts=None)
        repo.put(release1)
        repo.commit()

        a = collection.find_one({"_id": release1.id.id})
        assert a["state"] == RootAggState.REMOVED.value

    def test_get_one(self, arrepo, release1):
        db, repo = arrepo
        repo.put(release1)
        repo.commit()

        res = repo.get(release1.id)
        assert res
        assert len(res.events) == 0
        assert_result_equality(res, release1)

    def test_get_all(self, arrepo, release1, release2):
        db, repo = arrepo
        repo.put(release1)
        repo.put(release2)
        repo.commit()

        ress = repo.all()
        assert len(ress) == 2
