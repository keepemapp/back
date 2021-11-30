from abc import ABC, abstractmethod
from typing import NoReturn

from kpm.shared.domain import DomainRepository


class UseCase(ABC):
    pass


class Query(UseCase):
    def __init__(self, *, repository: DomainRepository):
        self.__repository = repository


class CommandOld(UseCase):
    def __init__(
        self, *, repository: DomainRepository
    ):
        self._repository = repository

    @abstractmethod
    def execute(self) -> NoReturn:
        raise NotImplementedError
