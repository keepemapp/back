import re
from dataclasses import dataclass, field
from typing import List, Optional

from emo.shared.domain import (AssetId, Event, RootAggregate, UserId,
                               ValueObject)


class AssetTtileException(Exception):
    """Exception to raise when title is not valid"""

    def __init__(self):
        super().__init__("Asset name is not valid")


class EmptyOwnerException(Exception):
    """ " Exception to raise when owner list is empty"""

    def __init__(self):
        super().__init__("Asset must have owners")


@dataclass(frozen=True, eq=True)
class FileData(ValueObject):
    name: str
    location: str
    type: str


@dataclass
class Asset(RootAggregate):
    """ """

    created_at: int
    owners_id: List[UserId]
    file: FileData
    id: AssetId
    title: Optional[str]
    description: Optional[str]
    _events: Optional[List[Event]] = field(default_factory=list)

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
            raise AssetTtileException()

    def has_expired(self) -> bool:
        """Returns true if asset has expired an is no longer valid

        TODO implement me
        """
        return False
