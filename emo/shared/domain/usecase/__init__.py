from dataclasses import dataclass
from datetime import datetime
from typing import Type
from abc import ABC, abstractmethod

from emo.settings import settings
from emo.shared.domain import *
from emo.shared.domain.usecase import Event


class UseCase(ABC):
    pass


class Query(UseCase):
    pass


class Command(UseCase):

    @abstractmethod
    def execute(self) -> Type[Event]:
        raise NotImplementedError


@dataclass(frozen=True)
class Event(UseCase):
    eventType: str
    aggregate: Type[Entity]
    occurredOn: datetime = datetime.utcnow()
    application: str = settings.APPLICATION_TECHNICAL_NAME
