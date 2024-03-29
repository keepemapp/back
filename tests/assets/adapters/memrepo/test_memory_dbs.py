import random
import string

import pytest

from kpm.assets.adapters.memrepo import MemoryPersistedAssetRepository
from kpm.assets.domain.model import Asset
from kpm.shared.domain.model import AssetId, UserId
from kpm.shared.domain.time_utils import now_utc_millis
from tests.assets.domain import asset, valid_asset


@pytest.fixture
def asset_repo(tmpdir) -> MemoryPersistedAssetRepository:
    file_name = "".join(random.choice(string.ascii_letters) for _ in range(10))
    f = tmpdir.mkdir("data").join(f"{file_name}.pk")
    return MemoryPersistedAssetRepository(dbfile=f)


@pytest.mark.unit
class TestAssetRepo:
    def test_init(self, tmpdir):
        f = tmpdir.mkdir("data").join("assetsrepo1.pk")
        r = MemoryPersistedAssetRepository(dbfile=f)
        assert not r.find_by_id(AssetId("someId"))
        assert not r.find_by_ownerid(UserId("someUserId"))
        assert not r.all()

    def test_init_string(self):
        r = MemoryPersistedAssetRepository(dbfile="sometestfile.pk")

    def test_create(self, tmpdir, asset):
        f = tmpdir.mkdir("data").join("assetsrepo2.pk")
        r = MemoryPersistedAssetRepository(dbfile=f)
        a = asset
        r.create(a)
        r.commit()
        assert f.exists()
        assert len(r.all()) == 1
        assert r.all()[0] == a

    def test_persists_at_commit(self, tmpdir, asset):
        f = tmpdir.mkdir("data").join("assetsrepo2.pk")
        r = MemoryPersistedAssetRepository(dbfile=f)
        a = asset
        r.create(a)
        r.commit()

        del r
        r = MemoryPersistedAssetRepository(dbfile=f)
        assert r.all()[0] == a

    def test_cannot_create_two_assets_same_id(self, asset_repo, asset):
        r = asset_repo
        a = asset
        r.create(a)
        r.commit()
        assert len(r.all()) == 1
        assert r.all()[0] == a

        with pytest.raises(Exception):
            r.create(a)
            r.commit()

    def test_find_by_id(self, asset_repo, asset):
        r = asset_repo
        a = asset
        r.create(a)
        r.commit()
        assert r.find_by_id(a.id) == a

    def test_find_by_id_returns_none_when_not_matching(
        self, asset_repo, asset
    ):
        r = asset_repo
        a = asset
        r.create(a)
        r.commit()
        assert not r.find_by_id(AssetId("nonexsiting id"))

    def test_find_multiple_ids(self, asset_repo, valid_asset, asset):
        r = asset_repo
        a = asset
        r.create(a)
        r.commit()
        valid_asset["id"] = AssetId("asset2id")
        a2 = Asset(**valid_asset)
        r.create(a2)
        r.commit()

        assert len(r.all()) == 2

        assert r.find_by_ids([a.id]) == [a]
        assert r.find_by_ids([a.id, a2.id]) == [a, a2]

        assert r.find_by_ids([a.id, AssetId("nonexsiting id")]) == [a]
        assert not r.find_by_ids([AssetId("nonexsiting id")])

    def test_visible_filter(self, asset_repo, asset):
        # Given
        r = asset_repo
        a = asset

        # When
        a.hide(now_utc_millis())
        r.create(a)
        r.commit()

        # Then
        assert len(r.all()) == 1
        assert not r.find_by_id(a.id)
        assert r.find_by_id(a.id, visible_only=False)
        assert len(r.find_by_ownerid(a.owners_id[0])) == 0

    def test_asset_type_filter(self, asset_repo, asset):
        # Given
        r = asset_repo
        a = asset
        r.create(a)
        r.commit()
        oid = a.owners_id[0]
        # Then
        assert len(r.find_by_ownerid(oid, asset_types=[])) == 1
        assert len(r.find_by_ownerid(oid, asset_types=[a.file.type])) == 1
        assert len(r.find_by_ownerid(oid, asset_types=["notype"])) == 0

        with pytest.raises(TypeError):
            r.find_by_ownerid(oid, asset_types=23)

    def test_by_owner_id(self, asset_repo, valid_asset):
        r = asset_repo
        a = Asset(**valid_asset)
        r.create(a)
        r.commit()

        valid_asset["id"] = AssetId("asset2id")
        first_user = valid_asset["owners_id"][0]
        second_user = UserId("userTwo")
        valid_asset["owners_id"] = [first_user, second_user]
        a2 = Asset(**valid_asset)
        r.create(a2)

        assert len(r.all()) == 2
        assert r.find_by_ownerid(second_user) == [a2]
        assert r.find_by_ownerid(first_user) == [a, a2]
        assert not r.find_by_ownerid(UserId("other user not there"))

    def test_delete(self, asset_repo, valid_asset):
        r = asset_repo
        a = Asset(**valid_asset)
        r.create(a)
        assert len(r.all()) == 1

        r.remove(a.id)
        assert not r.all()

    def test_delete_non_existing_asset(self, asset_repo, valid_asset):
        r = asset_repo
        a = Asset(**valid_asset)
        r.create(a)
        assert len(r.all()) == 1

        valid_asset["id"] = AssetId("asset2id")
        a2 = Asset(**valid_asset)

        r.remove(a2.id)
        assert len(r.all()) == 1

    def test_delete_by_id_non_existing(self, asset_repo, valid_asset):
        r = asset_repo
        a = Asset(**valid_asset)
        r.create(a)
        assert len(r.all()) == 1

        r.remove(AssetId("Asset not existing"))
        assert len(r.all()) == 1
