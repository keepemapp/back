from kpm.assets.adapters.filestorage import AssetFileLocalRepository
from kpm.assets.adapters.memrepo import (
    MemoryPersistedAssetRepository,
    MemPersistedReleaseRepo,
)
from kpm.assets.adapters.mongo.repository import (
    AssetMongoRepo,
    AssetReleaseMongoRepo,
)
from kpm.assets.adapters.s3 import AssetFileS3Repository
from kpm.assets.domain import model
from kpm.assets.domain.repositories import AssetFileRepository
from kpm.settings import settings as s
from kpm.shared.adapters.memrepo import MemoryUoW
from kpm.shared.adapters.mongo import MongoUoW
from kpm.shared.log import logger
from kpm.shared.service_layer.message_bus import UoWs


def uows() -> UoWs:
    if s.MONGODB_URL:
        logger.debug(
            f"Initializing Mongo Repositories",
            component="mongo",
        )
        return UoWs(
            {
                model.Asset: MongoUoW(AssetMongoRepo),
                model.AssetRelease: MongoUoW(AssetReleaseMongoRepo),
            }
        )
    else:

        logger.warn(
            "Initializing in-memory repositories. ONLY FOR DEVELOPMENT",
            component="api",
        )
        return UoWs(
            {
                model.Asset: MemoryUoW(MemoryPersistedAssetRepository),
                model.AssetRelease: MemoryUoW(MemPersistedReleaseRepo),
            }
        )


def asset_file_repository() -> AssetFileRepository:
    if s.ASSET_S3_ACCESS and s.ASSET_S3_SECRET:
        logger.debug(
            f"Initializing S3 repo at {s.ASSET_S3_URL}", component="s3"
        )
        return AssetFileS3Repository()
    else:
        logger.warn(
            "Initializing local disk repositories. ONLY FOR DEVELOPMENT",
            component="api",
        )
        return AssetFileLocalRepository()
