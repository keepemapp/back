import pytest

from kpm.shared.adapters.memrepo import MemoryUoW
from kpm.shared.entrypoints import bootstrap
from kpm.shared.service_layer.message_bus import UoWs
from kpm.users.domain.model import User
from kpm.users.service_layer import COMMAND_HANDLERS, EVENT_HANDLERS
from tests.users.utils import MemoryUserRepository


@pytest.fixture
def bus():
    """Init test bus for passing it to tests"""
    return bootstrap.bootstrap(
        uows=UoWs(
            {
                User: MemoryUoW(MemoryUserRepository),
            }
        ),
        event_handlers=EVENT_HANDLERS,
        command_handlers=COMMAND_HANDLERS,
    )
