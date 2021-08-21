from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import NoReturn

from emo import settings
from emo.shared.domain import Entity
from emo.shared.domain.usecase import UseCase


@dataclass(frozen=True)
class Event(UseCase):
    eventType: str
    aggregate: Entity
    occurredOn: datetime = datetime.utcnow()
    application: str = settings.APPLICATION_TECHNICAL_NAME


class EventPublisher(ABC):
    """
    Represents the Event bus interface
    """

    @abstractmethod
    def publish(self, event: Event) -> NoReturn:
        raise NotImplementedError
