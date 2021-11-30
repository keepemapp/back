from typing import List, NoReturn

from kpm.shared.domain import Event
from kpm.shared.domain.usecase import EventPublisher


class MemoryEventBus(EventPublisher):
    events: List[Event] = []

    def publish(self, event: Event) -> NoReturn:
        self.events.append(event)
