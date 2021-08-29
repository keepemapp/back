from dataclasses import dataclass
from typing import NoReturn, Type

from emo.assets.domain.entity.transfer_repository import TransferRepository
from emo.shared.domain import Tombstone, TransferId
from emo.shared.domain.usecase import Command, Event, EventPublisher


@dataclass(frozen=True)
class TransferDeleted(Event):
    eventType: str = "transfer_deleted"


class DeleteTransfer(Command):
    """
    Delete existing tansfer that has not happened yet

    Input: Tansfer ID
    Output: TransferDeleted event

    Rules:
    1. The person deleting it must own the transfer
    2. Transfer must be in the future
    """

    def __init__(
        self,
        *,
        transfer_id: TransferId,
        repository: Type[TransferRepository],
        message_bus: Type[EventPublisher]
    ):
        super().__init__(repository=repository, message_bus=message_bus)
        transfer = self._repository.find_by_id(id=transfer_id)
        if not transfer:
            raise Exception("Transfer does not exist")
        elif not transfer.is_future():
            raise Exception("Cannot delete past transfers")
        # TODO check for transfer ownership
        self._entity = Tombstone(transfer_id)
        self._event = TransferDeleted(aggregate=self._entity)

    def execute(self) -> NoReturn:
        self._repository.delete(self._entity.id)
        self._message_bus.publish(self._event)
