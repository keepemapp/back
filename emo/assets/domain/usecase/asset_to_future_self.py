from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

import emo.assets.domain.entity.asset_release as r
from emo.shared.domain import AssetId, Command, UserId
from emo.shared.domain.time_utils import to_millis
from emo.shared.domain.usecase.unit_of_work import AbstractUnitOfWork


@dataclass(frozen=True)
class CreateAssetToFutureSelf(Command):
    asset_ids: List[str]
    owner: str
    scheduled_date: datetime
    name: str
    description: Optional[str] = None


def create_asset_future_self(
    cmd: CreateAssetToFutureSelf, assetrelease_uow: AbstractUnitOfWork
):
    """
    Save away some assets that will be reappear in a later point in time
    in the individuals account

    Rules:
    1. The person using it must own the assets
        QUESTION: Must uniquely own them?
    2. Receiver must be the same as transferor
    3. scheduled date must be in the future

    TODO Return event that will be picked up by another
        handler to actually act on the files themselves if needed.
        here we act only on the assets metadata

    What happens:
    1. Check asset owner is the one sending the command
    2. Check is unique owner (???)
    3. Check asset does not have any "event" on it
       (it's not hidden for example)
    4. Change visibility status so it does not appear
    5. Event created/sent to store it to its repo


    :param cmd: command
    :type cmd: CreateTimeCapsule
    :param assetrelease_uow:
    :return:
    """
    with assetrelease_uow as uow:
        rel = r.AssetRelease(
            name=cmd.name,
            description=cmd.description,
            owner=UserId(cmd.owner),
            receivers=[UserId(cmd.owner)],
            assets=[AssetId(a) for a in cmd.asset_ids],
            release_type="asset_future_self",
            conditions=[r.TimeCondition(to_millis(cmd.scheduled_date))],
        )
        uow.repo.put(rel)
        uow.commit()
