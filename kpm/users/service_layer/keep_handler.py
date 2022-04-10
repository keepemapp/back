import kpm.users.domain.commands as cmds
import kpm.users.domain.events as events
import kpm.users.domain.model as model
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import RootAggState, UserId
from kpm.shared.service_layer.unit_of_work import AbstractUnitOfWork
from kpm.users.domain.repositories import KeepRepository


def new_keep(cmd: cmds.RequestKeep, keep_uow: AbstractUnitOfWork):
    requester = UserId(cmd.requester)
    requested = UserId(cmd.requested)
    with keep_uow as uow:
        repo: KeepRepository = uow.repo
        if repo.exists(requester, requested, all_states=True):
            # Allow to request back the keep if declined by mistake
            mutual_keeps = [k for k in repo.all(requester)
                           if k.requester == requested
                           or k.requested == requested]
            if len(mutual_keeps) == 2 \
                    or mutual_keeps[0].state != RootAggState.REMOVED:
                raise model.DuplicatedKeepException()
        k = model.Keep(
            id=DomainId(cmd.id),
            created_ts=cmd.timestamp,
            name_by_requester=cmd.name_by_requester,
            requester=requester,
            requested=requested,
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


def add_referral_keep_when_user_activated(
    event: events.UserActivated,
    keep_uow: AbstractUnitOfWork,
    user_uow: AbstractUnitOfWork,
):
    new_user_id = event.aggregate_id
    with user_uow:
        new_user: model.User = user_uow.repo.get(UserId(id=new_user_id))
        referral_user_id = new_user.referred_by
        print("user referred by")
    if referral_user_id:
        request_cmd = cmds.RequestKeep(
            requester=new_user_id, requested=referral_user_id
        )
        new_keep(request_cmd, keep_uow)
