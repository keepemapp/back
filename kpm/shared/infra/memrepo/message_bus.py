from typing import NoReturn

from kpm.shared.domain import Event
from kpm.shared.domain.usecase import EventPublisher


class NoneEventPub(EventPublisher):
    def publish(self, event: Event) -> NoReturn:
        pass
