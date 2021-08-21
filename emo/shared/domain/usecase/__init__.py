from abc import abstractmethod
from typing import NoReturn


from emo.shared.domain import *
from emo.shared.domain.usecase import Event
from emo.shared.domain.usecase.event import Event, EventPublisher


class UseCase(ABC):
    pass


class Query(UseCase):
    def __init__(self, *, repository: DomainRepository):
        self.__repository = repository


class Command(UseCase):

    def __init__(self, *, repository: DomainRepository, message_bus: EventPublisher):
        self._repository = repository
        self._message_bus = message_bus

    @abstractmethod
    def execute(self) -> NoReturn:
        raise NotImplementedError


