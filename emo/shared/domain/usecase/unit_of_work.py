from __future__ import annotations

from abc import ABC, abstractmethod
from typing import NoReturn

from emo.shared.domain import DomainRepository


class AbstractUnitOfWork(ABC):
    repo: DomainRepository

    def __enter__(self):
        return self

    def __exit__(self, *args) -> NoReturn:
        self.rollback()

    def commit(self) -> NoReturn:
        self._commit()

    def collect_new_events(self):
        for entity in self.repo.seen:
            while entity.events:
                yield entity.events.pop(0)
        # TODO test this... because events are saved to the Repo
        # but they should not be!

    @abstractmethod
    def _commit(self) -> NoReturn:
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> NoReturn:
        raise NotImplementedError


