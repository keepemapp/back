from __future__ import annotations

from typing import (
    Callable,
    Dict,
    List,
    NoReturn,
    Optional,
    Type,
    TypeVar,
    Union,
)

from kpm.shared.domain.commands import Command
from kpm.shared.domain.events import Event
from kpm.shared.domain.model import RootAggregate
from kpm.shared.log import logger
from kpm.shared.service_layer.unit_of_work import AbstractUnitOfWork

Message = Union[Command, Event]

UOWT = TypeVar("UOWT", bound=AbstractUnitOfWork)


class UoWs(Dict[Type[RootAggregate], AbstractUnitOfWork]):
    def collect_new_events(self) -> List[Event]:
        res = []
        for uow in self.values():
            res.extend(uow.collect_new_events())
        return res

    def as_dependencies(self) -> Dict[str, AbstractUnitOfWork]:
        return {k.__name__.lower() + "_uow": v for k, v in self.items()}


class MessageBus:
    """Handles events and commands

    It receives one command or event, executes its associated handlers
    (functions) and then retrieves the resulting events generated by the domain
    (see `self.queue` and the lines extending it)
    and executes them until there are no more events to process.

    From https://github.com/Dev-Nebe/architecture-patterns-with-python/blob/e3de63c922c2094d63949949b4cdf776fb5462dc/src/allocation/service_layer/messagebus.py # noqa: E501
    """

    def __init__(
        self,
        uows: UoWs,
        event_handlers: Dict[Type[Event], List[Callable]],
        command_handlers: Dict[Type[Command], Callable],
    ):
        self.uows: UoWs = uows
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers
        self.queue = []

    def handle(self, message: Message) -> Optional[NoReturn]:
        """Handles an event or command

        If the command fails, it raises the error
        If an event fails, it does nothing
        """
        logger.debug(f"Handling initial message {message}")
        self.queue = [message]
        while self.queue:
            message = self.queue.pop(0)
            if isinstance(message, Event):
                self.handle_event(message)
            elif isinstance(message, Command):
                self.handle_command(message)
            else:
                raise Exception(f"{message} was not an Event or Command")

    def handle_event(self, event: Event) -> None:
        logger.debug(self.event_handlers[type(event)])
        for handler in self.event_handlers[type(event)]:
            try:
                logger.debug(
                    '{"handler":"%s", "event":"%s"}', handler.__name__, event
                )
                handler(event)
                self.queue.extend(self.uows.collect_new_events())
                logger.debug(f"Extended queue to {self.queue}")
            except Exception:
                logger.exception(
                    '{"level": "ERROR", "handler":"%s", "event":"%s"}',
                    handler.__name__,
                    event,
                )
                continue  # TODO not sure we have to continue here

    def handle_command(self, command: Command) -> Optional[NoReturn]:
        try:
            handler = self.command_handlers[type(command)]
            logger.debug(
                '{"handler":"%s", "command":"%s"}', handler.__name__, command
            )
            handler(command)
            self.queue.extend(self.uows.collect_new_events())
        except Exception as e:
            logger.exception('{"command":"%s"}', command)
            raise e
