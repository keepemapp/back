from kpm.assets.adapters.filestorage import AssetFileRepository
from kpm.assets.adapters.memrepo import (
    MemoryPersistedAssetRepository,
    MemPersistedReleaseRepo,
)
from kpm.assets.adapters.mongo.repository import AssetMongoRepo, \
    AssetReleaseMongoRepo
from kpm.assets.domain import model
from kpm.shared.adapters.memrepo import MemoryUoW
from kpm.shared.adapters.mongo import MongoUoW
from kpm.shared.log import logger
from kpm.shared.service_layer.message_bus import UoWs
from kpm.settings import settings as s


def uows() -> UoWs:
    if s.MONGODB_URL:
        logger.info(f"Initializing Mongo Repositories at {s.MONGODB_URL}")
        return UoWs({
                model.Asset: MongoUoW(AssetMongoRepo),
                model.AssetRelease: MongoUoW(AssetReleaseMongoRepo),
            })
    else:

        logger.warn("Initializing in-memory repositories. ONLY FOR DEVELOPMENT")
        return UoWs(
            {
                model.Asset: MemoryUoW(MemoryPersistedAssetRepository),
                model.AssetRelease: MemoryUoW(MemPersistedReleaseRepo),
            }
        )


def asset_file_repository() -> AssetFileRepository:
    yield AssetFileRepository()
