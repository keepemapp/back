from datetime import datetime
from typing import Optional, List, Type


from emo.shared.domain import TransferId, Tombstone
from emo.shared.domain.usecase import Command
from emo.domain.entity.transfer import Transfer, TransferRepository
from emo.domain.usecase.transfer import TransferDeleted


class DeleteTransfer(Command):
    """
    Delete existing tansfer that has not happened yet

    Input: Tansfer ID
    Output: TransferDeleted event

    Rules:
    1. The person deleting it must own the transfer
    2. Transfer must be in the future
    """

    def __init__(self, transfer_id: TransferId, repo: Type[TransferRepository]):
        transfer = repo.find_by_id(id=transfer_id)
        if not transfer:
            raise Exception("Transfer does not exist")
        elif not transfer.is_future():
            raise Exception("Cannot delete past transfers")
        # TODO check for transfer ownership
        self.event = TransferDeleted(aggregate=Tombstone(transfer_id))

    def execute(self) -> TransferDeleted:
        return self.event
