import random

import kpm.assets.domain.commands as cmds
import kpm.assets.domain.model as model
from kpm.assets.domain.model import Asset
from kpm.assets.service_layer.unit_of_work import AssetUoW
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import AssetId, UserId
from kpm.shared.domain.time_utils import now_utc_millis
from kpm.shared.service_layer.unit_of_work import AbstractUnitOfWork


def create_asset_in_a_bottle(
    cmd: cmds.CreateAssetInABottle, assetrelease_uow: AbstractUnitOfWork
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
    with assetrelease_uow as uow:
        scheduled_date = random.randint(cmd.min_date, cmd.max_date)
        rel = model.AssetRelease(
            id=DomainId(cmd.aggregate_id),
            name=cmd.name,
            description=cmd.description,
            owner=UserId(cmd.owner),
            receivers=[UserId(u) for u in cmd.receivers],
            assets=[AssetId(a) for a in cmd.assets],
            release_type="asset_future_self",
            conditions=[model.TimeCondition(release_ts=scheduled_date)],
        )
        uow.repo.put(rel)
        uow.commit()


def create_asset_future_self(
    cmd: cmds.CreateAssetToFutureSelf, assetrelease_uow: AbstractUnitOfWork
):
    """
    Save away some assets that will be reappear in a later point in time
    in the individuals account

    Rules:
    1. The person using it must own the assets
        QUESTION: Must uniquely own them?
    2. Receiver must be the same as transferor
    3. scheduled date must be in the future

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
        rel = model.AssetRelease(
            id=DomainId(cmd.aggregate_id),
            name=cmd.name,
            description=cmd.description,
            owner=UserId(cmd.owner),
            receivers=[UserId(cmd.owner)],
            assets=[AssetId(a) for a in cmd.assets],
            release_type="asset_future_self",
            conditions=[model.TimeCondition(release_ts=cmd.scheduled_date)],
        )
        uow.repo.put(rel)
        uow.commit()


def trigger_release(
    cmd: cmds.TriggerRelease, assetrelease_uow: AbstractUnitOfWork
):
    """

    :param cmd: command
    :type cmd: CreateTimeCapsule
    :param assetrelease_uow:
    :return:
    """
    with assetrelease_uow as uow:
        rel: model.AssetRelease = uow.repo.get(DomainId(cmd.aggregate_id))
        if rel.can_trigger():
            rel.release()
            uow.repo.put(rel)
            uow.commit()


def cancel_release(
    cmd: cmds.CancelRelease, assetrelease_uow: AbstractUnitOfWork
):
    """

    :param cmd: command
    :type cmd: CreateTimeCapsule
    :param assetrelease_uow:
    :return:
    """
    with assetrelease_uow as uow:
        rel: model.AssetRelease = uow.repo.get(DomainId(cmd.aggregate_id))
        rel.cancel()
        uow.repo.put(rel)
        uow.commit()


def stash_asset(cmd: cmds.Stash, assetrelease_uow: AbstractUnitOfWork):
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


def create_time_capsule(
    cmd: cmds.CreateTimeCapsule, assetrelease_uow: AbstractUnitOfWork
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


def transfer_asset(cmd: cmds.TransferAssets, asset_uow: AssetUoW):
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
