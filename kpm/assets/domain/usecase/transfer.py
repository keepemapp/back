from dataclasses import dataclass, field
from typing import List

from kpm.assets.domain.entity.asset import Asset
from kpm.assets.domain.usecase.unit_of_work import AssetUoW
from kpm.shared.domain import AssetId, Command, init_id
from kpm.shared.domain.time_utils import now_utc_millis


@dataclass(frozen=True)
class TransferAssets(Command):
    """"""

    asset_ids: List[str]
    name: str
    owner: str
    receivers: List[str]
    description: str = None
    aggregate_id: str = field(default_factory=lambda: init_id().id)


def transfer_asset(cmd: TransferAssets, asset_uow: AssetUoW):
    """
    Changes the ownership of a group of assets

    Rules:
    1. The person using it must own the assets
        QUESTION: Must uniquely own them?
    2. Happens "immediately"

    TODO Return event that will be picked up by another
        handler to actually act on the files themselves if needed.
        here we act only on the assets metadata

    :param TransferAssets cmd: command
    :param AssetUoW asset_uow:
    :return:
    """
    with asset_uow as uow:
        mod_ts = now_utc_millis()
        for aid in cmd.asset_ids:
            a: Asset = uow.repo.find_by_id(AssetId(aid))
            a.change_owner(mod_ts, cmd.owner, cmd.receivers)
        uow.commit()
