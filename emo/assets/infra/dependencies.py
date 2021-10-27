from typing import Type

from emo.assets.domain.entity import AssetRepository
from emo.assets.domain.usecase.unit_of_work import AssetUoW
from emo.assets.infra.bootstrap import bootstrap
from emo.assets.infra.filestorage import AssetFileRepository
from emo.assets.infra.memrepo.repository import MemoryPersistedAssetRepository
from emo.assets.infra.memrepo.unit_of_work import AssetMemoryUnitOfWork
from emo.shared.domain.usecase.message_bus import MessageBus


def asset_repository() -> AssetRepository:
    yield MemoryPersistedAssetRepository()


def message_bus() -> MessageBus:
    yield bootstrap()


def unit_of_work_class() -> Type[AssetUoW]:
    yield AssetMemoryUnitOfWork


def asset_file_repository() -> AssetFileRepository:
    yield AssetFileRepository()
