import pytest

from kpm.users.domain.entity.users import User
from kpm.users.adapters.memrepo.repository import MemoryPersistedUserRepository
from tests.users.domain import *


@pytest.mark.unit
class TestUserRepo:
    def test_init(self, tmpdir, active_user):
        f = tmpdir.mkdir("data").join("usersrepo.pk")
        r = MemoryPersistedUserRepository(dbfile=str(f))
        assert len(r.all()) == 0

    def test_create(self, tmpdir, active_user):
        f = tmpdir.mkdir("data").join("usersrepo.pk")
        r = MemoryPersistedUserRepository(dbfile=str(f))
        u = User(**active_user)
        r.create(u)
        assert len(r.all()) == 1
        assert f.exists()

        # Assert we persist at create
        del r
        r = MemoryPersistedUserRepository(dbfile=str(f))
        assert len(r.all()) == 1

    def test_get_id(self, tmpdir, active_user):
        f = tmpdir.mkdir("data").join("usersrepo.pk")
        r = MemoryPersistedUserRepository(dbfile=str(f))
        u = User(**active_user)
        r.create(u)

        assert r.get(u.id) == u

    def test_update(self, tmpdir, active_user):
        f = tmpdir.mkdir("data").join("usersrepo.pk")
        r = MemoryPersistedUserRepository(dbfile=str(f))
        u = User(**active_user)
        r.create(u)

        u.disable()
        r.update(u)
        r.get(u.id).is_disabled()
        assert len(r.all()) == 1
        assert r.get(u.id).is_disabled()

        # Assert we persist at create
        del r
        r = MemoryPersistedUserRepository(dbfile=str(f))
        assert r.get(u.id).is_disabled()
