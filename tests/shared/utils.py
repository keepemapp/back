from typing import List, NoReturn

from emo.shared.domain.usecase import Event, EventPublisher


class MemoryEventBus(EventPublisher):
    events: List[Event] = []

    def publish(self, event: Event) -> NoReturn:
        self.events.append(event)
