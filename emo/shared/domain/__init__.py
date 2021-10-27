from __future__ import annotations

import abc
from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List, Optional, Protocol, Set, Type, TypeVar
from uuid import uuid4

from emo.settings import settings


@dataclass(frozen=True)
class DomainId:
    id: str

    def __eq__(self, other):
        return self.id == other.id

    # def __str__(self):
    #     return id


@dataclass(frozen=True)
class UserId(DomainId):
    pass


@dataclass(frozen=True)
class AssetId(DomainId):
    pass


@dataclass(frozen=True)
class TransferId(DomainId):
    pass


def init_id(id_type: Callable) -> DomainId:
    return id_type(id=str(uuid4()))


class IdTypeException(Exception):
    """Raise when ID type is not valid"""

    def __init__(self):
        super().__init__("ID Type is not valid")


@dataclass(frozen=True)
class Event:
    eventType: str = None
    aggregate: Entity = None
    occurredOn: datetime = datetime.utcnow()
    application: str = settings.APPLICATION_TECHNICAL_NAME


@dataclass(frozen=True)
class Command:
    pass


@dataclass
class Entity:
    id: DomainId

    def _id_type_is_valid(self, t: Type[DomainId], field: DomainId = None):
        """Raises Error if types do not match

        :param t: desired type
        :param field: value to compare to. By default, `self.id`
        :raises: IdTypeException
        """
        if not field:
            field = self.id
        if not isinstance(field, t):
            raise IdTypeException()

    def erase_sensitive_data(self) -> Entity:
        """
        Returns the entity with the sensitive data erased.
        Classes using it MUST implement it
        :return: self without sensitive information
        """
        raise NotImplementedError
        return self

    def __eq__(self, other) -> bool:
        return type(self) == type(other) and self.id == other.id


@dataclass
class RootAggregate(Entity):
    # _events: Optional[List[Event]]

    @property
    def events(self) -> List[Event]:
        """Property returning events to process

        :return: List of events
        :rtype: List[Event]
        """
        return self._events


@dataclass(frozen=True, eq=True)
class ValueObject:
    pass


class DomainRepository(ABC):
    """
    Represents the repository.

    It contains a `seen` variable that will allow us to collect all the
    events from every entity acted on.
    """

    @property
    def seen(self) -> Set[RootAggregate]:
        return self._seen


@dataclass
class Tombstone(Entity):
    """
    Special entity marking the deletion of an entity
    To be used with Deletion events
    TODO is this tombstone technique correct? I feel this is layer corruption
    """

    pass
