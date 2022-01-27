from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from kpm.shared.domain.events import Event
from kpm.shared.domain.repository import DomainRepository


class AbstractUnitOfWork(ABC):
    repo: DomainRepository

    def __init__(self):
        self._events: List[Event] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not exc_type:
            # Graceful exit
            pass
        else:
            self.rollback()

    def commit(self):
        self._events.extend(self._collect_events_from_entities())
        self._commit()

    def _collect_events_from_entities(self):
        for entity in self.repo.seen:
            while entity.events:
                yield entity.events.pop(0)

    def collect_new_events(self):
        while self._events:
            yield self._events.pop(0)

    @abstractmethod
    def _commit(self):
        raise NotImplementedError

    @abstractmethod
    def rollback(self):
        raise NotImplementedError
