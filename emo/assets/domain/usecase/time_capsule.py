from dataclasses import dataclass, field
from typing import List

from emo.shared.domain import Command, init_id
from emo.shared.domain.usecase.unit_of_work import AbstractUnitOfWork


@dataclass(frozen=True)
class CreateTimeCapsule(Command):
    asset_ids: List[str]
    name: str
    description: str
    owners_id: List[str]
    aggregate_id: str = field(default_factory=lambda: init_id().id)


def create_time_capsule(
    cmd: CreateTimeCapsule, assetrelease_uow: AbstractUnitOfWork
):
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
