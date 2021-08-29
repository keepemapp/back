from dataclasses import dataclass

from emo.shared.domain.usecase import Event


@dataclass(frozen=True)
class AssetDeleted(Event):
    eventType: str = "asset_deleted"


@dataclass(frozen=True)
class TransferCreated(Event):
    # TODO How we change the ID of the assets transfereds??
    # Do we maintain the same ID, or create a new one?
    eventType: str = "transfer_created"
