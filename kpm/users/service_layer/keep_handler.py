import kpm.users.domain.commands as cmds
import kpm.users.domain.events as events
import kpm.users.domain.model as model
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import UserId
from kpm.shared.service_layer.unit_of_work import AbstractUnitOfWork
from kpm.users.domain.repositories import KeepRepository


def new_keep(cmd: cmds.RequestKeep, keep_uow: AbstractUnitOfWork):
    with keep_uow as uow:
        repo: KeepRepository = uow.repo
        if repo.exists(
            UserId(cmd.requester), UserId(cmd.requested), all_states=True
        ):
            raise model.DuplicatedKeepException()
        k = model.Keep(
            id=DomainId(cmd.id),
            created_ts=cmd.timestamp,
            name_by_requester=cmd.name_by_requester,
            requester=UserId(cmd.requester),
            requested=UserId(cmd.requested),
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
        repo.put(k)
        uow.commit()


def decline_keep(cmd: cmds.DeclineKeep, keep_uow: AbstractUnitOfWork):
    with keep_uow as uow:
        repo: KeepRepository = uow.repo
        k = repo.get(kid=DomainId(cmd.keep_id))
        if cmd.by not in (k.requested.id, k.requester.id):
            raise model.KeepActionError()
        k.decline(UserId(cmd.by), cmd.reason, cmd.timestamp)
        repo.put(k)
        uow.commit()


def remove_all_keeps_of_user(
    event: events.UserRemoved, keep_uow: AbstractUnitOfWork
):
    user = UserId(id=event.aggregate_id)
    reason = "User has been removed."
    with keep_uow as uow:
        repo: KeepRepository = uow.repo
        ks = repo.all(user=user)
        for k in ks:
            k.decline(by_id=user, reason=reason, mod_ts=event.timestamp)
            repo.put(k)
        uow.commit()
