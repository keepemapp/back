from dataclasses import dataclass, field
from typing import List

import kpm.assets.domain.entity.asset_release as r
from kpm.shared.domain import AssetId, Command, DomainId, UserId, init_id
from kpm.shared.domain.usecase.unit_of_work import AbstractUnitOfWork


@dataclass(frozen=True)
class CreateAssetToFutureSelf(Command):
    assets: List[str]
    owner: str
    """UNIX timestamp in milliseconds"""
    scheduled_date: int
    name: str
    description: str = None
    aggregate_id: str = field(default_factory=lambda: init_id().id)


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
            id=DomainId(cmd.aggregate_id),
            name=cmd.name,
            description=cmd.description,
            owner=UserId(cmd.owner),
            receivers=[UserId(cmd.owner)],
            assets=[AssetId(a) for a in cmd.assets],
            release_type="asset_future_self",
            conditions=[r.TimeCondition(cmd.scheduled_date)],
        )
        uow.repo.put(rel)
        uow.commit()
