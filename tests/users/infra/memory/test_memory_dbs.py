import pytest

from emo.shared.domain.usecase import Event
from emo.users.domain.entity.users import User
from emo.users.infra.memrepo.message_bus import NoneEventPub
from emo.users.infra.memrepo.repository import MemoryPersistedUserRepository
from tests.users.domain import valid_user


@pytest.mark.unit
class TestEventPub:
    def test_add_event(self):
        p = NoneEventPub()
        p.publish(Event())


@pytest.mark.unit
class TestUserRepo:
    def test_init(self, tmpdir, valid_user):
        f = tmpdir.mkdir("data").join("usersrepo.pk")
        r = MemoryPersistedUserRepository(dbfile=str(f))
        assert len(r.all()) == 0

    def test_create(self, tmpdir, valid_user):
        f = tmpdir.mkdir("data").join("usersrepo.pk")
        r = MemoryPersistedUserRepository(dbfile=str(f))
        u = User(**valid_user)
        r.create(u)
        assert len(r.all()) == 1
        assert f.exists()

        # Assert we persist at create
        del r
        r = MemoryPersistedUserRepository(dbfile=str(f))
        assert len(r.all()) == 1

    def test_get_id(self, tmpdir, valid_user):
        f = tmpdir.mkdir("data").join("usersrepo.pk")
        r = MemoryPersistedUserRepository(dbfile=str(f))
        u = User(**valid_user)
        r.create(u)

        assert r.get(u.id) == u

    def test_update(self, tmpdir, valid_user):
        f = tmpdir.mkdir("data").join("usersrepo.pk")
        r = MemoryPersistedUserRepository(dbfile=str(f))
        u = User(**valid_user)
        r.create(u)

        disabled = u.disable()
        r.update(disabled)
        assert len(r.all()) == 1
        assert r.get(u.id).disabled

        # Assert we persist at create
        del r
        r = MemoryPersistedUserRepository(dbfile=str(f))
        assert r.get(u.id).disabled
