from typing import List, NoReturn

from emo.shared.domain import Event
from emo.shared.domain.usecase import EventPublisher


class MemoryEventBus(EventPublisher):
    events: List[Event] = []

    def publish(self, event: Event) -> NoReturn:
        self.events.append(event)
