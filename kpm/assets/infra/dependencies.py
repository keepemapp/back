from typing import Callable

from kpm.assets.domain.entity import AssetRepository
from kpm.assets.domain.usecase.unit_of_work import AssetUoW
from kpm.assets.infra.bootstrap import bootstrap
from kpm.assets.infra.filestorage import AssetFileRepository
from kpm.assets.infra.memrepo.repository import (
    MemoryPersistedAssetRepository, MemPersistedReleaseRepo)
from kpm.shared.domain.usecase.message_bus import MessageBus
from kpm.shared.infra.memrepo.unit_of_work import MemoryUoW


def asset_repository() -> AssetRepository:
    yield MemoryPersistedAssetRepository()


def message_bus() -> MessageBus:
    yield bootstrap()


def unit_of_work_class() -> Callable[[None], AssetUoW]:
    yield lambda **kwargs: MemoryUoW(MemoryPersistedAssetRepository)


def release_uow() -> Callable[[None], AssetUoW]:
    yield lambda **kwargs: MemoryUoW(MemPersistedReleaseRepo)


def asset_file_repository() -> AssetFileRepository:
    yield AssetFileRepository()