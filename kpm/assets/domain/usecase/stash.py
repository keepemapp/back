from dataclasses import dataclass, field
from typing import Dict, List

from kpm.shared.domain import Command, init_id
from kpm.shared.domain.usecase.unit_of_work import AbstractUnitOfWork


@dataclass(frozen=True)
class Stash(Command):
    """ """

    asset_ids: List[str]
    location: Dict  # TODO have a good location class
    name: str
    description: str
    owner: str
    receivers: List[str]
    aggregate_id: str = field(default_factory=lambda: init_id().id)


def stash_asset(cmd: Stash, assetrelease_uow: AbstractUnitOfWork):
    """
    Hide an asset in a geographical location. Once a person gets near it, it
    will discover it and take ownership.

    Concepts: stashing, hiding, geocatching

    Rules:
    1. The person using it must own the assets
        QUESTION: Must uniquely own them?
    2. If there are no receivers, it's open to anyone
    3. scheduled date must be in the future

    TODO Return event that will be picked up by another
        handler to actually act on the files themselves if needed.
        here we act only on the assets metadata

    :param cmd: command
    :type cmd: Stash
    :param uow:
    :return:
    """
    raise NotImplementedError
