from dataclasses import dataclass

import kpm.assets.domain.entity.asset_release as r
from kpm.shared.domain import Command, DomainId
from kpm.shared.domain.usecase.unit_of_work import AbstractUnitOfWork


@dataclass(frozen=True)
class TriggerRelease(Command):
    aggregate_id: str


def trigger_release(cmd: TriggerRelease, assetrelease_uow: AbstractUnitOfWork):
    """

    :param cmd: command
    :type cmd: CreateTimeCapsule
    :param assetrelease_uow:
    :return:
    """
    with assetrelease_uow as uow:
        rel: r.AssetRelease = uow.repo.get(DomainId(cmd.aggregate_id))
        if rel.can_trigger():
            rel.release()
            uow.repo.put(rel)
            uow.commit()


@dataclass(frozen=True)
class CancelRelease(Command):
    aggregate_id: str


def cancel_release(cmd: TriggerRelease, assetrelease_uow: AbstractUnitOfWork):
    """

    :param cmd: command
    :type cmd: CreateTimeCapsule
    :param assetrelease_uow:
    :return:
    """
    with assetrelease_uow as uow:
        rel: r.AssetRelease = uow.repo.get(DomainId(cmd.aggregate_id))
        rel.cancel()
        uow.repo.put(rel)
        uow.commit()
