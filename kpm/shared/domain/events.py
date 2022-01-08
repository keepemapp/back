from dataclasses import dataclass, field

from kpm.settings import settings
from kpm.shared.domain import IDT, required_field
from kpm.shared.domain.time_utils import now_utc_millis


@dataclass(frozen=True)
class Event:
    eventType: str = required_field()  # type: ignore
    aggregate_id: IDT = required_field()  # type: ignore
    timestamp: int = field(default_factory=now_utc_millis)
    application: str = settings.APPLICATION_TECHNICAL_NAME
