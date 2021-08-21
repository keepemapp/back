from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Type, Any
from uuid import uuid4
from abc import ABC


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
    id: DomainId

    def _validate_id_type(self, t: Type[DomainId]):
        return isinstance(self.id, t)

    def __post_init__(self):
        if not self._validate_id_type(DomainId):
            raise ValueError("ID is not of correct type")

    def erase_sensitive_data(self) -> Entity:
        """
        Returns the entity with the sensitive data erased.
        Classes using it MUST implement it
        :return: self without sensitive information
        """
        raise NotImplementedError
        return self

    def __eq__(self, other) -> bool:
        return self.id == other.id and type(self) == type(other)


@dataclass(frozen=True)
class RootAggregate(Entity):
    pass


@dataclass(frozen=True, eq=True)
class ValueObject:
    value: Any


class DomainRepository(ABC):
    """
    Represents the repository
    """

    pass


@dataclass(frozen=True)
class Tombstone(Entity):
    """
    Special entity marking the deletion of an entity
    To be used with Deletion events
    TODO is this tombstone technique correct? I feel this is layer corruption
    """

    pass
