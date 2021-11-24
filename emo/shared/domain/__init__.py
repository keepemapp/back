from __future__ import annotations

from abc import ABC
from dataclasses import Field, dataclass, field
from enum import Enum, unique
from typing import Callable, Dict, List, Set, Type, TypeVar
from uuid import uuid4

from dataclasses_json import dataclass_json

from emo.settings import settings
from emo.shared.domain.time_utils import current_utc_millis


def required_field() -> Field:
    def raise_err():
        raise TypeError()

    return field(default_factory=lambda: raise_err)


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


def init_id(id_type: Callable = DomainId) -> DomainId:
    return id_type(id=str(uuid4()))


class IdTypeException(Exception):
    """Raise when ID type is not valid"""

    def __init__(self):
        super().__init__("ID Type is not valid")


IDT = TypeVar("IDT", str, DomainId)


@dataclass_json
@dataclass(frozen=True)
class Event:
    eventType: str = required_field()
    aggregate_id: IDT = required_field()
    timestamp: int = field(default_factory=current_utc_millis)
    application: str = settings.APPLICATION_TECHNICAL_NAME


@dataclass_json
@dataclass(frozen=True)
class Command:
    pass


@dataclass_json
@dataclass
class Entity:
    id: DomainId = init_id(DomainId)

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


class NoValue(Enum):
    def __repr__(self):
        return str(self.value)


@unique
class RootAggState(NoValue):
    ACTIVE = "active"
    PENDING_VALIDATION = "pending_validation"
    HIDDEN = "hidden"
    INACTIVE = "inactive"
    REMOVED = "removed"


@dataclass
class RootAggregate(Entity):
    """Base class with parameters that will need to be overwritten"""

    _events: List[Event] = field(default_factory=list)
    created_ts: int = current_utc_millis()
    modified_ts: Dict[str, int] = field(default_factory=dict)
    state: RootAggState = RootAggState.ACTIVE

    @property
    def events(self) -> List[Event]:
        """Property returning events to process

        :return: List of events
        :rtype: List[Event]
        """
        return self._events

    def _update_field(self, mod_ts: int, field: str, value):
        if mod_ts >= self._modified_ts_for(field):
            setattr(self, field, value)
            self.modified_ts[field] = mod_ts

    def _modified_ts_for(self, field: str):
        return self.modified_ts.get(field, self.created_ts)


@dataclass_json
@dataclass(frozen=True, eq=True)
class ValueObject:
    pass


class DomainRepository(ABC):
    """
    Represents the repository.

    It contains a `seen` variable that will allow us to collect all the
    events from every entity acted on.
    """

    def __init__(self, **kwargs):
        pass

    @property
    def seen(self) -> Set[RootAggregate]:
        return self._seen
