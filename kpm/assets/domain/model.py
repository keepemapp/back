from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import asdict, field
from enum import unique
from typing import Dict, List, Optional, Set, Union

from pydantic.dataclasses import dataclass

from kpm.assets.domain.events import (
    AssetOwnershipChanged,
    AssetReleaseCanceled,
    AssetReleased,
    AssetReleaseScheduled,
)
from kpm.shared.domain import (
    DomainId,
    init_id,
    required_field,
    updatable_field,
)
from kpm.shared.domain.model import (
    AssetId,
    NoValue,
    RootAggregate,
    RootAggState,
    UserId,
    ValueObject,
)
from kpm.shared.domain.time_utils import now_utc_millis


class AssetTitleException(Exception):
    """Exception to raise when title is not valid"""

    def __init__(self, msg: str = None):
        if not msg:
            msg = "Asset title is not valid"
        super().__init__(msg)


class EmptyOwnerException(Exception):
    """ " Exception to raise when owner list is empty"""

    def __init__(self):
        super().__init__("Asset must have owners")


class AssetOwnershipException(Exception):
    def __init__(self):
        super().__init__("You are not the owner of the asset")


@dataclass(frozen=True, eq=True)
class FileData(ValueObject):
    name: str
    location: str
    type: str
    "Size of the data in BYTES. It will get double checked"
    size_bytes: int


UIDT = Union[UserId, str]


@dataclass
class Asset(RootAggregate):
    """ """

    owners_id: List[UserId] = required_field()  # type: ignore
    file: FileData = required_field()  # type: ignore
    id: AssetId = required_field()  # type: ignore
    title: str = updatable_field(default="")  # type: ignore
    description: Optional[str] = updatable_field(default="")  # type: ignore
    state: RootAggState = field(default=RootAggState.PENDING)
    tags: Optional[Set[str]] = updatable_field(default_factory=set)  # type: ignore  # noqa:E501
    people: Optional[Set[str]] = updatable_field(default_factory=set)  # type: ignore  # noqa:E501
    """Optional String indicating the place where this asset happened"""
    location: Optional[str] = updatable_field(default=None)  # type: ignore
    """Optional string to indicate the date where this asset happened"""
    created_date: Optional[str] = updatable_field(default=None)  # type: ignore
    # TODO change me
    extra_private: bool = updatable_field(default=False)  # type: ignore
    bookmarked: bool = updatable_field(default=False)  # type: ignore

    @staticmethod
    def _title_is_valid(name: str) -> bool:
        """Validates asset title

        :param name: str:

        """
        regex = r"^[\w][\w ?!'¿¡*-\.\[\]\{\}\(\)]{0,64}$"
        return True if re.match(regex, name) else False

    def __post_init__(self, loaded_from_db: bool):
        self._id_type_is_valid(AssetId)
        if not self.owners_id:
            raise EmptyOwnerException()
        for uid in self.owners_id:
            self._id_type_is_valid(UserId, uid)
        if not self._title_is_valid(self.title):
            raise AssetTitleException(
                "Title too long or containing too many thigns"
            )

        if not loaded_from_db:
            # Send asset creation event
            pass

    def hide(self, mod_ts: Optional[int]):
        self._update_field(mod_ts, "state", RootAggState.HIDDEN)

    def show(self, mod_ts: Optional[int]):
        self._update_field(mod_ts, "state", RootAggState.ACTIVE)

    def is_visible(self) -> bool:
        return self.state in [RootAggState.ACTIVE, RootAggState.PENDING]

    def upload_file(self, mod_ts: int):
        self._update_field(mod_ts, "state", RootAggState.ACTIVE)

    def change_owner(
        self, mod_ts: Optional[int], transferor: UIDT, new: List[UIDT]
    ):
        """Changes asset ownership

        Raises `AssetOwnershipException` if the transferor does not own
        the asset.
        If the new owners are already in the original list, it does nothing.

        :param mod_ts:
        :param transferor:
        :param new:
        :return:
        """
        transferor = self._to_uid(transferor)
        if transferor not in self.owners_id:
            raise AssetOwnershipException()

        if all(n in self.owners_id for n in new):
            return
        news = [o for o in self.owners_id if o != transferor]
        news.extend(self._to_uids(new))
        updated = self._update_field(mod_ts, "owners_id", news)
        if updated:
            self.events.append(
                AssetOwnershipChanged(
                    aggregate_id=self.id.id,
                    timestamp=self.modified_ts["owners_id"],
                    owners=[uid.id for uid in self.owners_id],
                )
            )

    @staticmethod
    def _to_uid(uid: UIDT):
        return UserId(uid) if isinstance(uid, str) else uid

    @staticmethod
    def _to_uids(uids: List[UIDT]):
        return [Asset._to_uid(u) for u in uids]

    def __hash__(self):
        return hash(self.id.id)


@dataclass(frozen=True, eq=True)
class ReleaseCondition(ValueObject, ABC):
    type: str

    @abstractmethod
    def is_met(self, context=None) -> bool:
        if context is None:
            context = {}
        raise NotImplementedError


@dataclass(frozen=True, eq=True)
class TrueCondition(ReleaseCondition):
    type: str = "true_condition"

    def is_met(self, context=None) -> bool:
        return True


@dataclass(frozen=True, eq=True)
class TimeCondition(ReleaseCondition):
    release_ts: int = required_field()
    type: str = "time_condition"

    def is_met(self, context=None) -> bool:
        return self.release_ts < now_utc_millis()


@dataclass(frozen=True, eq=True)
class GeographicalCondition(ReleaseCondition):
    location: str = required_field()
    type: str = "geographical_condition"

    def is_met(self, context=None) -> bool:
        if context is None:
            context = {}
        guess = (context.get("location", "") or "").lower().replace(" ", "")
        return self.location.lower().replace(" ", "") == guess


def dict_to_release_cond(condition: Dict) -> ReleaseCondition:
    cond_type = condition.get("type").lower()
    if cond_type == "true_condition":
        return TrueCondition(**condition)
    elif cond_type == "time_condition":
        return TimeCondition(**condition)
    elif cond_type == "geographical_condition":
        return GeographicalCondition(**condition)
    else:
        raise TypeError("Condition type not recognized")


@unique
class BequestType(NoValue):
    """The sender looses access to the assets"""

    GIFT = "gitft"
    """All the users will co-own the assets"""
    CO_OWNSRSHIP = "co-ownership"
    """Duplication of assets. Copying the entities."""
    COPY = "copy"
    """Asset to one self"""
    SELF = "self"


@dataclass
class AssetRelease(RootAggregate):
    """It represents an event that will trigger the transfer (release) of an
    asset to its receivers.

    Only the owner of this event can act on it.
    """

    name: str = required_field()  # type: ignore
    description: Optional[str] = field(default=None)  # type: ignore
    owner: UserId = required_field()  # type: ignore
    receivers: List[UserId] = required_field()  # type: ignore
    assets: List[AssetId] = required_field()  # type: ignore
    conditions: List[ReleaseCondition] = required_field()  # type: ignore
    release_type: str = required_field()  # type: ignore
    bequest_type: BequestType = required_field()  # type: ignore
    id: DomainId = field(default_factory=lambda: init_id(DomainId))

    def __post_init__(self, loaded_from_db: bool):
        self._assert_conditions_compatibility()
        if not loaded_from_db:
            self.events.append(
                AssetReleaseScheduled(
                    aggregate_id=self.id.id,
                    re_conditions=self._conditons_dict(),
                    re_type=self.release_type,
                    owner=self.owner.id,
                    assets=[a.id for a in self.assets],
                    receivers=[u.id for u in self.receivers],
                )
            )

    def _assert_conditions_compatibility(self):
        # TODO implement ?
        pass

    def _conditons_dict(self):
        dict = {}
        for c in self.conditions:
            dict.update(asdict(c))
        return dict

    def is_active(self) -> bool:
        return self.state == RootAggState.ACTIVE

    def is_past(self) -> bool:
        return self.state in [RootAggState.INACTIVE, RootAggState.REMOVED]

    def can_trigger(self, context: Dict = None) -> bool:
        """If all the condition are met, returns `True`."""
        if not self.is_active():
            return False
        return all([c.is_met(context) for c in self.conditions])

    def trigger(self, context: Dict = None):
        if not self.can_trigger(context):
            raise OperationTriggerException()
        ts = now_utc_millis()
        self._update_field(ts, "state", RootAggState.INACTIVE)
        self.events.append(
            AssetReleased(
                aggregate_id=self.id.id,
                timestamp=ts,
                re_type=self.release_type,
                bequest_type=self.bequest_type.value,
                owner=self.owner.id,
                assets=[a.id for a in self.assets],
                receivers=[u.id for u in self.receivers],
            )
        )

    def cancel(self, reason: str = None):
        """Cancels the event."""
        ts = now_utc_millis()
        self._update_field(ts, "state", RootAggState.REMOVED)
        self.events.append(
            AssetReleaseCanceled(
                aggregate_id=self.id.id,
                timestamp=ts,
                assets=[a.id for a in self.assets],
                reason=reason,
            )
        )

    def __hash__(self):
        return hash(self.id.id)


class OperationTriggerException(Exception):
    def __init__(self):
        super().__init__()
        self.msg = "Legacy operation cannot be triggered."


class DuplicatedAssetReleaseException(Exception):
    def __init__(self):
        super().__init__()
        self.msg = "You cannot create two asset releases with the same name."


class DuplicatedAssetException(Exception):
    def __init__(self):
        super().__init__()
        self.msg = (
            "You have tried creating the same asset "
            + "twice. This is not allowed. "
            + "Try updating it."
        )
