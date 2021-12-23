from typing import Callable

from fastapi import Depends

from kpm.assets.adapters.filestorage import AssetFileRepository
from kpm.assets.domain.model import Asset
from kpm.assets.entrypoints.bootstrap import bootstrap
from kpm.assets.service_layer.unit_of_work import AssetUoW
from kpm.shared.service_layer.message_bus import MessageBus


def message_bus() -> MessageBus:
    yield bootstrap()


def unit_of_work_class(
    bus: Depends(message_bus),
) -> Callable[[None], AssetUoW]:
    yield lambda **kwargs: bus.uows.get(Asset)


def asset_file_repository() -> AssetFileRepository:
    yield AssetFileRepository()
