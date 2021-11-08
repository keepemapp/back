from dataclasses import dataclass
from datetime import datetime
from typing import List

from emo.shared.domain.usecase.unit_of_work import AbstractUnitOfWork
from emo.shared.domain import Command


@dataclass(frozen=True)
class CreateAssetInABottle(Command):
    asset_ids: List[str]
    scheduled_date: datetime
    name: str
    description: str
    receivers_id: List[str]
    owner_id: str


def create_asset_in_a_bottle(cmd: CreateAssetInABottle,
                             assetrelease_uow: AbstractUnitOfWork):
    """
    Save away some assets that will be reappear in a later point in time
    to the desired receivers. All assets will be

    Rules:
    1. The person using it must own the assets
        QUESTION: Must uniquely own them?
    2. Receivers must exist (check that when "liberating" the asset. Fail if not)
    3. scheduled date must be in the future

    TODO Return event that will be picked up by another
        handler to actually act on the files themselves if needed.
        here we act only on the assets metadata

    :param cmd: command
    :type cmd: CreateAssetInABottle
    :param uow:
    :return:
    """
    raise NotImplementedError
