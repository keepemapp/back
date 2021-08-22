from typing import NoReturn

from emo.shared.domain.usecase import EventPublisher, Event


class NoneEventPub(EventPublisher):
    def publish(self, event: Event) -> NoReturn:
        pass
