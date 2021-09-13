from emo.assets.domain.entity import AssetRepository
from emo.assets.infra.memrepo.repository import MemoryPersistedAssetRepository


def asset_repository() -> AssetRepository:
    yield MemoryPersistedAssetRepository()
