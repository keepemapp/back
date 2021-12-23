from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, unique
from typing import Dict, List, Optional, Type

from kpm.shared.domain import DomainId, IdTypeException, init_id
from kpm.shared.domain.events import Event
from kpm.shared.domain.time_utils import now_utc_millis


@dataclass(frozen=True)
class UserId(DomainId):
    pass


@dataclass(frozen=True)
class AssetId(DomainId):
    pass


@dataclass(frozen=True)
class TransferId(DomainId):
    pass


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

    def __hash__(self):
        return hash(self.id)


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
    created_ts: int = now_utc_millis()
    modified_ts: Dict[str, int] = field(default_factory=dict)
    state: RootAggState = RootAggState.ACTIVE

    @property
    def events(self) -> List[Event]:
        """Property returning events.

        Do not access it directly if you are

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

    def last_modified(self) -> Optional[int]:
        """Returns last modified UNIX time in milliseconds"""
        if self.modified_ts:
            return max(self.modified_ts.values())
        else:
            return None


@dataclass(frozen=True, eq=True)
class ValueObject:
    pass
