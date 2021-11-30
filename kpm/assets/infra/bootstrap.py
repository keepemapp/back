import inspect
from typing import Callable, Dict, List, Type

from kpm.assets.domain.entity import asset, asset_release
from kpm.assets.domain.usecase import COMMAND_HANDLERS, EVENT_HANDLERS
from kpm.assets.infra.memrepo.repository import (
    MemoryPersistedAssetRepository, MemPersistedReleaseRepo)
from kpm.shared.domain import Command, Event
from kpm.shared.domain.usecase.message_bus import MessageBus, UoWs
from kpm.shared.infra.memrepo.unit_of_work import MemoryUoW

EventHandler = Dict[Type[Event], List[Callable]]
CommandHandler = Dict[Type[Command], Callable]


def bootstrap(
    asset_uow=MemoryUoW(MemoryPersistedAssetRepository),
    release_uow=MemoryUoW(MemPersistedReleaseRepo),
) -> MessageBus:

    uows = UoWs({
        asset.Asset: asset_uow,
        asset_release.AssetRelease: release_uow,
    })
    dependencies = {**uows.as_dependencies()}
    return MessageBus(
        uows=uows,
        event_handlers=injected_event_handlers(dependencies, EVENT_HANDLERS),
        command_handlers=injected_command_handlers(
            dependencies, COMMAND_HANDLERS
        ),
    )


def injected_event_handlers(
    dependencies: Dict, handlers: EventHandler
) -> EventHandler:
    return {
        event_type: [
            inject_dependencies(handler, dependencies)
            for handler in event_handlers
        ]
        for event_type, event_handlers in handlers.items()
    }


def injected_command_handlers(
    dependencies: Dict, handlers: CommandHandler
) -> CommandHandler:
    return {
        command_type: inject_dependencies(handler, dependencies)
        for command_type, handler in handlers.items()
    }


def inject_dependencies(handler, dependencies):
    params = inspect.signature(handler).parameters
    deps = {
        name: dependency
        for name, dependency in dependencies.items()
        if name in params
    }
    func = lambda message: handler(message, **deps)  # noqa: E731
    func.__name__ = handler.__name__
    return func
