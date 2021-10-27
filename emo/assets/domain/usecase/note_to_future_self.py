from dataclasses import dataclass
from datetime import datetime
from typing import List

from emo.assets.domain.usecase.unit_of_work import AssetUoW
from emo.shared.domain import Command


@dataclass(frozen=True)
class CreateNoteToFutureSelf(Command):
    asset_ids: List[str]
    scheduled_date: datetime
    name: str
    description: str
    owners_id: List[str]


def create_note_future_self(cmd: CreateNoteToFutureSelf, uow: AssetUoW):
    """
    Save away some assets that will be reappear in a later point in time
    in the individuals account

    Input: Scheduled date, assets, title(optional) and description(optional)
    Output: TransferCreated event

    Rules:
    1. The person using it must own the assets
        QUESTION: Must uniquelly own them?
    2. Receiver must be the same as transferor
    3. scheduled date must be in the future

    TODO Return event that will be picked up by another
        handler to actually act on the files themselves if needed.
        here we act only on the assets metadata

    :param cmd: command
    :type cmd: CreateTimeCapsule
    :param uow:
    :return:
    """
    raise NotImplementedError
