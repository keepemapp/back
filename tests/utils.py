from typing import NoReturn

from kpm.shared.domain import Event
from kpm.shared.domain.usecase import EventPublisher


class TestEventPublisher(EventPublisher):
    published_event = None

    def publish(self, event: Event) -> NoReturn:
        self.published_event = event
