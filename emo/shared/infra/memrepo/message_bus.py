from typing import NoReturn

from emo.shared.domain import Event
from emo.shared.domain.usecase import EventPublisher


class NoneEventPub(EventPublisher):
    def publish(self, event: Event) -> NoReturn:
        pass
