from typing import NoReturn

from emo.shared.domain.usecase import Event, EventPublisher


class NoneEventPub(EventPublisher):
    def publish(self, event: Event) -> NoReturn:
        pass
