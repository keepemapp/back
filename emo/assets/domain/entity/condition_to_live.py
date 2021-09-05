from dataclasses import dataclass
from typing import Optional

from emo.shared.domain import ValueObject
from emo.shared.domain.time_utils import current_utc_timestamp


@dataclass(frozen=True, eq=True)
class ConditionToLive(ValueObject):
    """
    Concept similar to time to live that can be expanded to other conditions.
    If one of the conditions is met, it will trigger an erasure behaviour.

    :param expiry_timestamp: int: timestamp of when the it expires
    """

    expiry_timestamp: Optional[int]

    def expired(self) -> bool:
        """Returns true of expiring conditions are met"""

        return (
            False
            if not self.expiry_timestamp
            else self.expiry_timestamp < current_utc_timestamp()
        )
