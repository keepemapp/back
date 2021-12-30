from kpm.assets.adapters.filestorage import AssetFileRepository
from kpm.assets.adapters.memrepo import MemPersistedReleaseRepo, \
    MemoryPersistedAssetRepository
from kpm.assets.domain import model
from kpm.shared.adapters.memrepo import MemoryUoW
from kpm.shared.service_layer.message_bus import UoWs


def uows() -> UoWs:
    return UoWs(
        {
            model.Asset: MemoryUoW(MemoryPersistedAssetRepository),
            model.AssetRelease: MemoryUoW(MemPersistedReleaseRepo),
        }
    )


def asset_file_repository() -> AssetFileRepository:
    yield AssetFileRepository()
