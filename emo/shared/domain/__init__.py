from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Type
from uuid import uuid4
from abc import ABC

from api import settings


@dataclass(frozen=True)
class DomainId:
    id: str


@dataclass(frozen=True)
class UserId(DomainId):
    pass


@dataclass(frozen=True)
class AssetId(DomainId):
    pass


@dataclass(frozen=True)
class TransferId(DomainId):
    pass


def init_id(id_type: Callable):
    return id_type(id=str(uuid4()))


@dataclass(frozen=True)
class Entity:
    id: Type[DomainId]


@dataclass(frozen=True)
class RootAggregate(Entity):
    id: Type[DomainId]

    def __eq__(self, other) -> bool:
        return self.id == other.id


@dataclass(frozen=True, eq=True)
class ValueObject:
    pass


class DomainRepository(ABC):
    pass


@dataclass(frozen=True)
class Tombstone(Entity):
    """
    Special entity marking the deletion of an entity
    To be used with Deletion events
    TODO is this tombstone technique correct? I feel this is layer corruption
    """
    pass
