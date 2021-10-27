from dataclasses import dataclass
from typing import List

from emo.assets.domain.usecase.unit_of_work import AssetUoW
from emo.shared.domain import Command


@dataclass(frozen=True)
class CreateTimeCapsule(Command):
    asset_ids: List[str]
    name: str
    description: str
    owners_id: List[str]


def create_time_capsule(cmd: CreateTimeCapsule, uow: AssetUoW):
    """
    Save away some assets that will be reappear in a later point in time
    to the individuals you specify.

    Rules:
    1. The person using it must own the assets
    2. scheduled date must be in the future

    TODO Return TimeCapsuleCreated event that will be picked up by another
        handler to actually act on the files themselves if needed
        here we act only on the assets metadata

    :param cmd: command
    :type cmd: CreateTimeCapsule
    :param uow:
    :return:
    """
    raise NotImplementedError
