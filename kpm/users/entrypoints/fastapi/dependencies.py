from kpm.shared.adapters.memrepo import MemoryUoW
from kpm.shared.service_layer.message_bus import UoWs
from kpm.users.adapters.memrepo.repository import MemoryPersistedUserRepository
from kpm.users.domain.model import User


def uows() -> UoWs:
    return UoWs(
        {
            User: MemoryUoW(MemoryPersistedUserRepository),
        }
    )
