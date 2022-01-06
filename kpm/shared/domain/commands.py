from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import NoReturn

from kpm.shared.domain.repository import DomainRepository
from kpm.shared.domain.time_utils import now_utc_millis


@dataclass(frozen=True)
class Command:
    timestamp: int = field(default_factory=now_utc_millis)


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
