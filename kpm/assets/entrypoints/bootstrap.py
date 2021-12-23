import inspect
from typing import Callable, Dict, List, Type

import kpm.assets.domain.model as model
from kpm.assets.adapters.memrepo.repository import (
    MemoryPersistedAssetRepository, MemPersistedReleaseRepo)
from kpm.assets.service_layer import COMMAND_HANDLERS, EVENT_HANDLERS
from kpm.shared.adapters.memrepo import MemoryUoW
from kpm.shared.domain.commands import Command
from kpm.shared.domain.events import Event
from kpm.shared.service_layer.message_bus import MessageBus, UoWs

EventHandler = Dict[Type[Event], List[Callable]]
CommandHandler = Dict[Type[Command], Callable]


def bootstrap(
    asset_uow=MemoryUoW(MemoryPersistedAssetRepository),
    release_uow=MemoryUoW(MemPersistedReleaseRepo),
) -> MessageBus:

    uows = UoWs(
        {
            model.Asset: asset_uow,
            model.AssetRelease: release_uow,
        }
    )
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
