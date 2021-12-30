import pytest

from kpm.shared.adapters.memrepo import MemoryUoW
from kpm.shared.entrypoints import bootstrap
from kpm.shared.service_layer.message_bus import UoWs
from kpm.users.domain.entity.users import User
from tests.users.utils import MemoryUserRepository


@pytest.fixture
def bus():
    """Init test bus for passing it to tests"""
    return bootstrap.bootstrap(uows=UoWs({
        User: MemoryUoW(MemoryUserRepository),
    }))
