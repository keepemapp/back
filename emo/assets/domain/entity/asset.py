import re
from dataclasses import dataclass
from typing import List, Union

from emo.shared.domain import (AssetId, RootAggregate, UserId, Event,
                               ValueObject, RootAggState, required_field)


@dataclass(frozen=True)
class AssetOwnershipChanged(Event):
    owners: List[str] = required_field()
    eventType: str = "AssetOwnershipChanged"


class AssetTitleException(Exception):
    """Exception to raise when title is not valid"""

    def __init__(self):
        super().__init__("Asset name is not valid")


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


UIDT = Union[UserId, str]


@dataclass
class Asset(RootAggregate):
    """ """
    owners_id: List[UserId] = required_field()
    file: FileData = required_field()
    id: AssetId = required_field()
    title: str = ""
    description: str = ""

    @staticmethod
    def _title_is_valid(name: str) -> bool:
        """Validates asset title

        :param name: str:

        """
        regex = r"^[\w][\w ?!'¿¡*-\.\[\]\{\}\(\)]{0,31}$"
        return True if re.match(regex, name) else False

    def __post_init__(self):
        self._id_type_is_valid(AssetId)
        if not self.owners_id:
            raise EmptyOwnerException()
        for uid in self.owners_id:
            self._id_type_is_valid(UserId, uid)
        if not self._title_is_valid(self.title):
            raise AssetTitleException()

    def hide(self, mod_ts: int):
        self._update_field(
            mod_ts,
            "state",
            RootAggState.HIDDEN
        )

    def show(self, mod_ts: int):
        self._update_field(
            mod_ts,
            "state",
            RootAggState.ACTIVE
        )

    def is_visible(self) -> bool:
        return self.state == RootAggState.ACTIVE

    def change_owner(self, mod_ts: int, transferor: UIDT, new: List[UIDT]):
        """ Changes asset ownership

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
        self._update_field(mod_ts, "owners_id", news)
        self.events.append(AssetOwnershipChanged(
            aggregate_id=self.id.id,
            timestamp=mod_ts,
            owners=[uid.id for uid in self.owners_id],
        ))

    @staticmethod
    def _to_uid(uid: UIDT):
        return UserId(uid) if isinstance(uid, str) else uid

    @staticmethod
    def _to_uids(uids: List[UIDT]):
        return [Asset._to_uid(u) for u in uids]
