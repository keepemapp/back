from typing import Type

from emo.assets.domain.entity import AssetRepository
from emo.assets.domain.usecase.unit_of_work import AssetUoW
from emo.assets.infra.bootstrap import bootstrap
from emo.assets.infra.filestorage import AssetFileRepository
from emo.assets.infra.memrepo.repository import (
    MemoryPersistedAssetRepository, MemPersistedReleaseRepo)
from emo.shared.domain.usecase.message_bus import MessageBus
from emo.shared.infra.memrepo.unit_of_work import MemoryUoW


def asset_repository() -> AssetRepository:
    yield MemoryPersistedAssetRepository()


def message_bus() -> MessageBus:
    yield bootstrap()


def unit_of_work_class() -> Type[AssetUoW]:
    yield lambda: MemoryUoW(MemoryPersistedAssetRepository)


def release_uow() -> Type[AssetUoW]:
    yield lambda: MemoryUoW(MemPersistedReleaseRepo)


def asset_file_repository() -> AssetFileRepository:
    yield AssetFileRepository()
