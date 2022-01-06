import kpm.users.domain.commands as cmds
import kpm.users.domain.model as model
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import UserId
from kpm.shared.service_layer.unit_of_work import AbstractUnitOfWork
from kpm.users.domain.repositories import KeepRepository


def new_keep(cmd: cmds.RequestKeep, keep_uow: AbstractUnitOfWork):
    with keep_uow as uow:
        repo: KeepRepository = uow.repo
        if repo.exists(UserId(cmd.requester), UserId(cmd.requested)):
            raise model.DuplicatedKeepException()
        k = model.Keep(
            created_ts=cmd.timestamp,
            name_by_requester=cmd.name_by_requester,
            requester=UserId(cmd.requester),
            requested=UserId(cmd.requested)
        )
        repo.put(k)
        uow.commit()


def accept_keep(cmd: cmds.AcceptKeep, keep_uow: AbstractUnitOfWork):
    with keep_uow as uow:
        repo: KeepRepository = uow.repo
        k = repo.get(kid=DomainId(cmd.keep_id))
        if cmd.by != k.requested.id:
            raise model.KeepActionError()
        k.accept(cmd.name_by_requested, cmd.timestamp)
        uow.commit()


def decline_keep(cmd: cmds.DeclineKeep, keep_uow: AbstractUnitOfWork):
    with keep_uow as uow:
        repo: KeepRepository = uow.repo
        k = repo.get(kid=DomainId(cmd.keep_id))
        k.decline(UserId(cmd.by), cmd.reason, cmd.timestamp)