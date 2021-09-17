from emo.assets.domain.entity import AssetRepository
from emo.assets.infra.filestorage import AssetFileRepository
from emo.assets.infra.memrepo.repository import MemoryPersistedAssetRepository


def asset_repository() -> AssetRepository:
    yield MemoryPersistedAssetRepository()


def asset_file_repository() -> AssetFileRepository:
    yield AssetFileRepository()
