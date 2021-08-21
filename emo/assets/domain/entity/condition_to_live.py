from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from emo.shared.domain import ValueObject


@dataclass(frozen=True, eq=True)
class ConditionToLive(ValueObject):
    """
    Concept similar to time to live that can be expanded to other conditions.
    If one of the conditions is met, it will trigger an erasure behaviour.
    """
    expiry_time: Optional[datetime]

    def condition_not_met(self) -> bool:
        return self.expiry_time < datetime.utcnow()

