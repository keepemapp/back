import inspect
from typing import Callable, Dict, List, Type

from kpm.assets.service_layer import COMMAND_HANDLERS, EVENT_HANDLERS
from kpm.shared.adapters.notifications import EmailNotifications, \
    NoNotifications
from kpm.shared.domain.commands import Command
from kpm.shared.domain.events import Event
from kpm.shared.service_layer.message_bus import MessageBus, UoWs
from kpm.settings import settings as s

EventHandler = Dict[Type[Event], List[Callable]]
CommandHandler = Dict[Type[Command], Callable]


def bootstrap(
    uows: UoWs,
) -> MessageBus:

    if s.EMAIL_SENDER_ADDRESS and s.EMAIL_SENDER_PASSWORD:
        email_notifications = EmailNotifications()
    else:
        email_notifications = NoNotifications()

    dependencies = {email_notifications: email_notifications,
                    **uows.as_dependencies()}
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
