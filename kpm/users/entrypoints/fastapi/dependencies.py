from kpm.settings import settings as s
from kpm.shared.adapters.memrepo import MemoryUoW
from kpm.shared.adapters.mongo import MongoUoW
from kpm.shared.service_layer.message_bus import UoWs
from kpm.users.adapters.memrepo.repository import (
    KeepMemoryRepository,
    MemoryPersistedUserRepository,
)
from kpm.users.adapters.mongo.repository import (
    KeepMongoRepo,
    SessionMongoRepo,
    UserMongoRepo,
)
from kpm.users.domain.model import Keep, Session, User


def uows() -> UoWs:
    if s.MONGODB_URL:
        return UoWs(
            {
                User: MongoUoW(UserMongoRepo),
                Keep: MongoUoW(KeepMongoRepo),
                Session: MongoUoW(SessionMongoRepo),
            }
        )
    return UoWs(
        {
            User: MemoryUoW(MemoryPersistedUserRepository),
            Keep: MemoryUoW(KeepMemoryRepository),
        }
    )
