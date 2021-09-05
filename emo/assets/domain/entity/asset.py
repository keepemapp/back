import re
from dataclasses import dataclass
from typing import List, Optional

from emo.assets.domain.entity.condition_to_live import ConditionToLive
from emo.shared.domain import AssetId, IdTypeException, RootAggregate, UserId


class AssetTtileException(Exception):
    """Exception to raise when title is not valid"""

    def __init__(self):
        super().__init__("Asset name is not valid")


class EmptyOwnerException(Exception):
    """ " Exception to raise when owner list is empty"""

    def __init__(self):
        super().__init__("Asset must have owners")


@dataclass(frozen=True)
class Asset(RootAggregate):
    """ """

    created_at: int
    owners_id: List[UserId]
    type: str
    file_name: str
    file_location: str
    id: AssetId
    title: Optional[str]
    description: Optional[str]
    conditionToLive: Optional[ConditionToLive]

    @staticmethod
    def _title_is_valid(name: str) -> bool:
        """Validates asset title

        :param name: str:

        """
        regex = r"^[\w][\w ?!'¿¡*-\.\[\]\{\}\(\)]{0,31}$"
        return True if re.match(regex, name) else False

    def __post_init__(self):
        super().__post_init__()
        if not self._id_type_is_valid(AssetId):
            raise IdTypeException()
        if not self.owners_id:
            raise EmptyOwnerException()
        for uid in self.owners_id:
            if not self._id_type_is_valid(UserId, uid):
                raise IdTypeException()
        if not self._title_is_valid(self.title):
            raise AssetTtileException()

    def has_expired(self) -> bool:
        """ """
        return (
            False
            if not self.conditionToLive
            else self.conditionToLive.expired()
        )
