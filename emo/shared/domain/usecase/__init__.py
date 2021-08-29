from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import NoReturn

from emo.settings import settings
from emo.shared.domain import DomainRepository, Entity


@dataclass(frozen=True)
class Event:
    eventType: str = None
    aggregate: Entity = None
    occurredOn: datetime = datetime.utcnow()
    application: str = settings.APPLICATION_TECHNICAL_NAME


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


class Command(UseCase):
    def __init__(
        self, *, repository: DomainRepository, message_bus: EventPublisher
    ):
        self._repository = repository
        self._message_bus = message_bus

    @abstractmethod
    def execute(self) -> NoReturn:
        raise NotImplementedError
