from dataclasses import InitVar, field, fields
from enum import Enum, unique
from typing import Any, Dict, List, Optional, Type

from pydantic.dataclasses import dataclass

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
    id: DomainId = field(default_factory=lambda: init_id(DomainId), hash=True)

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

    def erase_sensitive_data(self) -> "Entity":
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


class FrozenException(Exception):
    def __init__(self):
        super().__init__("This item is frozen/removed and can't be modified.")


class RemovalNotPossible(Exception):
    pass


@unique
class RootAggState(NoValue):
    ACTIVE = "active"
    PENDING = "pending"
    HIDDEN = "hidden"
    INACTIVE = "inactive"
    REMOVED = "removed"


VISIBLE_STATES = [
    RootAggState.ACTIVE,
    RootAggState.PENDING,
]

NOT_VISIBLE_STATES = [
    RootAggState.HIDDEN,
    RootAggState.INACTIVE,
    RootAggState.REMOVED,
]

FINAL_STATES = [
    RootAggState.INACTIVE,
    RootAggState.REMOVED,
]


@dataclass
class RootAggregate(Entity):
    """Base class with parameters that will need to be overwritten

    Extend it as adding fields with values.

    You can mark user updatable attributes adding the following content at
    field definitions:

    ```
    field(..., metadata={'user_updatable': True})

    from kpm.shared.domain import updatable_field
    updatable_field(...)
    ```
    """

    events: List[Event] = field(default_factory=list)
    created_ts: int = now_utc_millis()
    modified_ts: Dict[str, int] = field(default_factory=dict)
    state: RootAggState = RootAggState.ACTIVE
    loaded_from_db: InitVar[bool] = False

    class Config:
        underscore_attrs_are_private = True

    def update_fields(
        self, mod_ts: int, updates: Dict[str, Any], allow_all: bool = False
    ):
        """
        Updates internal fields that can be directly changed by the user
        :param mod_ts: when the change happens
        :param updates: dict with field_name, new_value
        :param allow_all: bool indicating if all fields can be updated
        """
        updated_pairs = []
        status_update = None
        for kv in updates.items():
            if kv[0] == "state":
                status_update = kv[1]
            elif kv[1] is not None:
                updated_pairs.append(kv)
        for f, value in updated_pairs:
            if not allow_all and f not in self._updatable_fields():
                raise AttributeError(f"Attribute '{f}' is not user updatable.")
            if not self.__isinstance(f, value):
                raise TypeError(f"Attribute '{f}' updated with wrong type. ")
        for f, value in updated_pairs:
            self._update_field(mod_ts, f, value)
        if status_update:
            if not self.__isinstance("state", status_update):
                raise TypeError(
                    f"Attribute '{status_update}' updated with wrong type. "
                )
            return self._update_field(mod_ts, "state", status_update)

    def __isinstance(self, field: str, value: Any) -> bool:
        """Support for generic types in isinstance

        TODO for now we deactivate it. There is a problem with annotations
        https://stackoverflow.com/questions/66006087/how-to-use-typing-get-type-hints-with-pep585-in-python3-8  # noqa: E501
        Let's go back when we support only python 3.9 or 3.10
        """
        # target_type = get_type_hints(self).get(field)
        # if "Set" in str(target_type):
        #     target_type = set
        # elif "List" in str(target_type):
        #     target_type = list
        # elif "Optional" in str(target_type):
        #     target_type = target_type.__args__[0]
        # return isinstance(value, target_type)
        return True

    def _updatable_fields(self):
        """Returns the list of user updatable fields.

        Those are the ones with the metadata `{'user_updatable': True}`
        """
        return [
            f.name
            for f in fields(self)
            if f.metadata.get("user_updatable", False)
        ]

    def _update_field(self, mod_ts: Optional[int], field: str, value) -> bool:
        """Updates a field and returns true if updated successfully

        It does not update it if mod_ts is older than the latest update for
        that field.
        """
        if self.state in FINAL_STATES:
            raise FrozenException()
        if mod_ts is None:
            mod_ts = now_utc_millis()
        is_newer = mod_ts >= self._modified_ts_for(field)
        if is_newer:
            setattr(self, field, value)
            self.modified_ts[field] = mod_ts
            return True
        return False

    def _modified_ts_for(self, field: str):
        return self.modified_ts.get(field, self.created_ts)

    def last_modified(self) -> Optional[int]:
        """Returns last modified UNIX time in milliseconds"""
        if self.modified_ts:
            return max(self.modified_ts.values())
        else:
            return None

    def is_visible(self):
        return self.state not in NOT_VISIBLE_STATES

    def remove(self, mod_ts: Optional[int], **kwargs):
        if self.state != FINAL_STATES:
            self._update_field(mod_ts, "state", RootAggState.REMOVED)


@dataclass(frozen=True, eq=True)
class ValueObject:
    pass


class UserNotAllowedException(Exception):
    pass
