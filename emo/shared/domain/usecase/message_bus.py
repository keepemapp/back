from __future__ import annotations

import logging
from typing import Callable, Dict, List, Type, Union

from emo.shared.domain import Command, Event
from emo.shared.domain.usecase.unit_of_work import AbstractUnitOfWork

logger = logging.getLogger(__name__)

Message = Union[Command, Event]


class MessageBus:
    """Handles events and commands

    From https://github.com/Dev-Nebe/architecture-patterns-with-python/blob/e3de63c922c2094d63949949b4cdf776fb5462dc/src/allocation/service_layer/messagebus.py # noqa: E501    """

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        event_handlers: Dict[Type[Event], List[Callable]],
        command_handlers: Dict[Type[Command], Callable],
    ):
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers
        self.queue = []

    def handle(self, message: Message):
        self.queue = [message]
        while self.queue:
            message = self.queue.pop(0)
            if isinstance(message, Event):
                self.handle_event(message)
            elif isinstance(message, Command):
                self.handle_command(message)
            else:
                raise Exception(f"{message} was not an Event or Command")

    def handle_event(self, event: Event):
        for handler in self.event_handlers[type(event)]:
            try:
                logger.debug(
                    "handling event %s with handler %s", event, handler
                )
                handler(event)
                self.queue.extend(self.uow.collect_new_events())
            except Exception:
                logger.exception("Exception handling event %s", event)
                continue  # TODO not sure we have to continue here

    def handle_command(self, command: Command):
        logger.debug("handling command %s", command)
        try:
            handler = self.command_handlers[type(command)]
            handler(command)
            self.queue.extend(self.uow.collect_new_events())
        except Exception as e:
            logger.exception("Exception handling command %s", command)
            raise e
