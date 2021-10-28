from dataclasses import dataclass
from typing import List, Dict

from emo.assets.domain.usecase.unit_of_work import AssetUoW
from emo.shared.domain import Command


@dataclass(frozen=True)
class TransferAssets(Command):
    """"""
    asset_ids: List[str]
    name: str
    description: str
    from_user: List[str]
    to_user: List[str]


def transfer_asset(cmd: TransferAssets, uow: AssetUoW):
    """
    Changes the ownership of a group of assets

    Rules:
    1. The person using it must own the assets
        QUESTION: Must uniquely own them?
    2. Happens "immediately"

    TODO Return event that will be picked up by another
        handler to actually act on the files themselves if needed.
        here we act only on the assets metadata

    :param cmd: command
    :type cmd: TransferAssets
    :param uow:
    :return:
    """
    raise NotImplementedError
