from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import NoReturn

from kpm.shared.domain.repository import DomainRepository


@dataclass(frozen=True)
class Command:
    pass


class UseCase(ABC):
    """Deprecated"""

    pass


class Query(UseCase):
    """Deprecated"""

    def __init__(self, *, repository: DomainRepository):
        self.__repository = repository


class CommandOld(UseCase):
    """Deprecated"""

    def __init__(self, *, repository: DomainRepository):
        self._repository = repository

    @abstractmethod
    def execute(self) -> NoReturn:
        raise NotImplementedError
