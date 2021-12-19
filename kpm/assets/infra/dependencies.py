from typing import Callable

from fastapi import Depends

from kpm.assets.domain.entity.asset import Asset
from kpm.assets.domain.usecase.unit_of_work import AssetUoW
from kpm.assets.infra.bootstrap import bootstrap
from kpm.assets.infra.filestorage import AssetFileRepository
from kpm.shared.domain.usecase.message_bus import MessageBus


def message_bus() -> MessageBus:
    yield bootstrap()


def unit_of_work_class(
    bus: Depends(message_bus),
) -> Callable[[None], AssetUoW]:
    yield lambda **kwargs: bus.uows.get(Asset)


def asset_file_repository() -> AssetFileRepository:
    yield AssetFileRepository()
