from kpm.shared.adapters.memrepo import MemoryUoW
from kpm.shared.adapters.mongo import MongoUoW
from kpm.shared.service_layer.message_bus import UoWs
from kpm.users.adapters.memrepo.repository import (
    KeepMemoryRepository,
    MemoryPersistedUserRepository,
)
from kpm.users.adapters.mongo.repository import KeepMongoRepo, UserMongoRepo
from kpm.users.domain.model import Keep, User

from kpm.settings import settings as s


def uows() -> UoWs:
    if s.MONGODB_URL:
        return UoWs({
                User: MongoUoW(UserMongoRepo),
                Keep: MongoUoW(KeepMongoRepo),
            })
    return UoWs(
        {
            User: MemoryUoW(MemoryPersistedUserRepository),
            Keep: MemoryUoW(KeepMemoryRepository),
        }
    )
