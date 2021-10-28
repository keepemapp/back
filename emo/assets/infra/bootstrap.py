import inspect
from typing import Callable, Dict, List, Type

from emo.assets.domain.usecase import COMMAND_HANDLERS, EVENT_HANDLERS
from emo.assets.domain.usecase.unit_of_work import AssetUoW
from emo.assets.infra.memrepo.unit_of_work import AssetMemoryUnitOfWork
from emo.shared.domain import Command, Event
from emo.shared.domain.usecase.message_bus import MessageBus

EventHandler = Dict[Type[Event], List[Callable]]
CommandHandler = Dict[Type[Command], Callable]


def bootstrap(
    uow: AssetUoW = AssetMemoryUnitOfWork(),
) -> MessageBus:

    dependencies = {"uow": uow}
    return MessageBus(
        uow=uow,
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
    l = lambda message: handler(message, **deps)
    l.__name__ = handler.__name__
    return l
