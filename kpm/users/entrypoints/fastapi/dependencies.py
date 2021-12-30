from kpm.shared.adapters.memrepo import MemoryUoW
from kpm.shared.service_layer.message_bus import UoWs
from kpm.users.domain.entity.users import User
from kpm.users.adapters.memrepo.repository import MemoryPersistedUserRepository


def uows() -> UoWs:
    return UoWs(
        {
            User: MemoryUoW(MemoryPersistedUserRepository),
        }
    )
