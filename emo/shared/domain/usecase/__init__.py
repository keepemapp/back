from abc import ABC, abstractmethod
from typing import NoReturn

from emo.shared.domain import DomainRepository, Event


class EventPublisher(ABC):
    """
    Represents the Event bus interface
    """

    @abstractmethod
    def publish(self, event: Event) -> NoReturn:
        raise NotImplementedError


class UseCase(ABC):
    pass


class Query(UseCase):
    def __init__(self, *, repository: DomainRepository):
        self.__repository = repository


class CommandOld(UseCase):
    def __init__(
        self, *, repository: DomainRepository, message_bus: EventPublisher
    ):
        self._repository = repository
        self._message_bus = message_bus

    @abstractmethod
    def execute(self) -> NoReturn:
        raise NotImplementedError
