from dataclasses import dataclass, field
from typing import List

from emo.shared.domain import Command, init_id
from emo.shared.domain.usecase.unit_of_work import AbstractUnitOfWork


@dataclass(frozen=True)
class CreateAssetInABottle(Command):
    assets: List[str]
    """UNIX timestamp in milliseconds"""
    scheduled_date: int
    name: str
    receivers: List[str]
    owner: str
    description: str = None
    aggregate_id: str = field(default_factory=init_id().id)


def create_asset_in_a_bottle(
    cmd: CreateAssetInABottle, assetrelease_uow: AbstractUnitOfWork
):
    """
    Save away some assets that will be reappear in a later point in time
    to the desired receivers. All assets will be

    Rules:
    1. The person using it must own the assets
        QUESTION: Must uniquely own them?
    2. Receivers must exist (check that when "liberating" the asset.
        Fail if not)
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
