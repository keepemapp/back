from dataclasses import dataclass
from typing import Dict, List

from emo.shared.domain import Command
from emo.shared.domain.usecase.unit_of_work import AbstractUnitOfWork


@dataclass(frozen=True)
class Stash(Command):
    """ """

    asset_ids: List[str]
    location: Dict  # TODO have a good location class
    name: str
    description: str
    from_users: List[str]
    to_users: List[str]


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
