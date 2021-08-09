from dataclasses import dataclass

from emo.shared.domain.usecase import Event


# TODO investigate more the problem with TypeError: non-default argument 'X' follows default argument
# It has no solution as of python 3.9, only workarounds
# See https://bugs.python.org/issue36077
@dataclass(frozen=True)
class TransferCreated(Event):
    # TODO How we change the ID of the assets transfereds??
    # Do we maintain the same ID, or create a new one?
    eventType: str = "transfer_created"


@dataclass(frozen=True)
class TransferDeleted(Event):
    eventType: str = "transfer_deleted"


@dataclass(frozen=True)
class TransferExecuted(Event):
    eventType = "transfer_executed"
