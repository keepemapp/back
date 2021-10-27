from typing import NoReturn

from emo.shared.domain import Event
from emo.shared.domain.usecase import EventPublisher


class TestEventPublisher(EventPublisher):
    published_event = None

    def publish(self, event: Event) -> NoReturn:
        self.published_event = event
