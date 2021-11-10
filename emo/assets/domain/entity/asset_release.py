from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Set


from emo.shared.domain import (AssetId, DomainId, DomainRepository, Event,
                               RootAggregate, RootAggState, UserId,
                               ValueObject, init_id, required_field, Command)
from emo.shared.domain.time_utils import current_utc_millis


@dataclass(frozen=True)
class AssetReleaseScheduled(Event):
    eventType: str = "AssetReleaseScheduled"
    re_conditions: List[ReleaseCondition] = required_field()
    re_type: str = required_field()
    owner: str = required_field()
    assets: List[str] = required_field()
    receivers: List[str] = required_field()


@dataclass(frozen=True)
class AssetReleaseCanceled(Event):
    eventType: str = "AssetReleaseCanceled"
    assets: List[str] = required_field()


@dataclass(frozen=True)
class AssetReleased(Event):
    eventType: str = "AssetReleased"
    re_type: str = required_field()
    owner: str = required_field()
    assets: List[str] = required_field()
    receivers: List[str] = required_field()


@dataclass(frozen=True, eq=True)
class ReleaseCondition(ValueObject, ABC):
    @abstractmethod
    def is_met(self) -> bool:
        raise NotImplementedError


@dataclass(frozen=True, eq=True)
class TrueCondition(ReleaseCondition):
    def is_met(self) -> bool:
        return True


@dataclass(frozen=True, eq=True)
class TimeCondition(ReleaseCondition):
    release_ts: int

    def is_met(self) -> bool:
        return self.release_ts < current_utc_millis()


@dataclass
class AssetRelease(RootAggregate):
    """It represents an event that will trigger the transfer (release) of an
    asset to its receivers.

    Only the owner of this event can act on it.
    """

    name: str = required_field()
    description: str = required_field()
    owner: UserId = required_field()
    receivers: List[UserId] = required_field()
    assets: List[AssetId] = required_field()
    conditions: List[ReleaseCondition] = required_field()
    release_type: str = required_field()
    id: DomainId = init_id(DomainId)

    def __post_init__(self):
        self._events.append(
            AssetReleaseScheduled(
                aggregate_id=self.id.id,
                re_conditions=self.conditions,
                re_type=self.release_type,
                owner=self.owner.id,
                assets=[a.id for a in self.assets],
                receivers=[u.id for u in self.receivers],
            )
        )

    def is_active(self) -> bool:
        return self.state == RootAggState.ACTIVE

    def is_past(self) -> bool:
        return self.state in [RootAggState.INACTIVE, RootAggState.REMOVED]

    def is_due(self) -> bool:
        """If all the condition are met, returns `True`."""
        return all([c.is_met() for c in self.conditions])

    def release(self):
        ts = current_utc_millis()
        self._update_field(ts, "state", RootAggState.INACTIVE)
        self._events.append(
            AssetReleased(
                aggregate_id=self.id.id,
                timestamp=ts,
                re_type=self.release_type,
                owner=self.owner.id,
                assets=[a.id for a in self.assets],
                receivers=[u.id for u in self.receivers],
            )
        )

    def cancel(self):
        """Cancels the event."""
        ts = current_utc_millis()
        self._update_field(ts, "state", RootAggState.REMOVED)
        self._events.append(
            AssetReleaseCanceled(
                aggregate_id=self.id.id,
                timestamp=ts,
                assets=[a.id for a in self.assets],
            )
        )

    def __hash__(self):
        return hash(self.id.id)


class AssetReleaseRepository(DomainRepository):
    def __init__(self):
        super().__init__()
        self._seen: Set[AssetRelease] = set()

    @abstractmethod
    def put(self, release: AssetRelease):
        raise NotImplementedError

    @abstractmethod
    def get(self, release_id: DomainId) -> AssetRelease:
        raise NotImplementedError

    @abstractmethod
    def user_active_releases(self, user_id: UserId) -> List[AssetRelease]:
        raise NotImplementedError

    @abstractmethod
    def user_past_releases(self, user_id: UserId) -> List[AssetRelease]:
        raise NotImplementedError

    @abstractmethod
    def all(self) -> List[AssetRelease]:
        raise NotImplementedError