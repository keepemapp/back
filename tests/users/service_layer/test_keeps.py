import pytest

from kpm.shared.domain.model import RootAggState
from kpm.users.domain import commands as cmds
import kpm.users.domain.model as model
from kpm.users.domain.repositories import KeepRepository
from tests.users.fixtures import bus


def create_user_cmd(uid: str = "1"):
    return cmds.RegisterUser(username=uid, password=uid,
                             email=f"{uid}@emailtest.com", user_id=uid)


@pytest.mark.unit
class TestKeepHandlers:
    def test_requesting_keep(self, bus):
        uid1 = "uid1"
        uid2 = "uid2"
        history = [
            create_user_cmd(uid1),
            create_user_cmd(uid2),
        ]
        for msg in history:
            bus.handle(msg)

        cmd = cmds.RequestKeep(requester=uid1, requested=uid2)
        bus.handle(cmd)

        # Then
        with bus.uows.get(model.Keep) as uow:
            repo: KeepRepository = uow.repo
            assert len(repo.all()) == 1
            assert repo.all()[0].state == RootAggState.PENDING

    def test_can_only_accept_existing(self, bus):
        with pytest.raises(AttributeError):
            cmd = cmds.AcceptKeep(keep_id="notexists", by="")
            bus.handle(cmd)

    def test_only_requested_can_accept(self, bus):
        uid1 = "uid1"
        uid2 = "uid2"
        history = [
            create_user_cmd(uid1),
            create_user_cmd(uid2),
            cmds.RequestKeep(requester=uid1, requested=uid2)
        ]
        for msg in history:
            bus.handle(msg)
        with bus.uows.get(model.Keep) as uow:
            kid = uow.repo.all()[0].id.id

        # When
        with pytest.raises(model.KeepActionError):
            cmd = cmds.AcceptKeep(keep_id=kid, by="another user")
            bus.handle(cmd)

        # When
        with pytest.raises(model.KeepActionError):
            cmd = cmds.AcceptKeep(keep_id=kid, by=uid1)
            bus.handle(cmd)

    def test_accepting_keep(self, bus):
        uid1 = "uid1"
        uid2 = "uid2"
        history = [
            create_user_cmd(uid1),
            create_user_cmd(uid2),
            cmds.RequestKeep(requester=uid1, requested=uid2)
        ]
        for msg in history:
            bus.handle(msg)
        with bus.uows.get(model.Keep) as uow:
            kid = uow.repo.all()[0].id.id

        # When
        cmd = cmds.AcceptKeep(keep_id=kid, by=uid2)
        bus.handle(cmd)

        # Then
        with bus.uows.get(model.Keep) as uow:
            repo: KeepRepository = uow.repo
            assert len(repo.all()) == 1
            assert repo.all()[0].state == RootAggState.ACTIVE

    def test_not_duplicating_requests(self, bus):
        uid1 = "uid1"
        uid2 = "uid2"
        history = [
            create_user_cmd(uid1),
            create_user_cmd(uid2),
            cmds.RequestKeep(requester=uid1, requested=uid2)
        ]
        for msg in history:
            bus.handle(msg)
        with bus.uows.get(model.Keep) as uow:
            kid = uow.repo.all()[0].id.id

        # When
        cmd = cmds.RequestKeep(requester=uid1, requested=uid2)
        with pytest.raises(model.DuplicatedKeepException):
            bus.handle(cmd)

        # Then
        with bus.uows.get(model.Keep) as uow:
            repo: KeepRepository = uow.repo
            assert len(repo.all()) == 1

    def test_declining_keep(self, bus):
        uid1 = "uid1"
        uid2 = "uid2"
        history = [
            create_user_cmd(uid1),
            create_user_cmd(uid2),
            cmds.RequestKeep(requester=uid1, requested=uid2)
        ]
        for msg in history:
            bus.handle(msg)
        with bus.uows.get(model.Keep) as uow:
            kid = uow.repo.all()[0].id.id

        # When
        with pytest.raises(model.KeepActionError):
            bus.handle(cmds.DeclineKeep(keep_id=kid, by="otherUs", reason=""))

        # When
        bus.handle(cmds.DeclineKeep(keep_id=kid, by=uid1, reason=""))

        # Then
        with bus.uows.get(model.Keep) as uow:
            repo: KeepRepository = uow.repo
            assert repo.all()[0].state == RootAggState.REMOVED

    def test_accepted_only_if_pending(self, bus):
        uid1 = "uid1"
        uid2 = "uid2"
        history = [
            create_user_cmd(uid1),
            create_user_cmd(uid2),
            cmds.RequestKeep(requester=uid1, requested=uid2)
        ]
        for msg in history:
            bus.handle(msg)
        with bus.uows.get(model.Keep) as uow:
            kid = uow.repo.all()[0].id.id
        bus.handle(cmds.DeclineKeep(keep_id=kid, by=uid1, reason=""))

        # When
        with pytest.raises(model.KeepAlreadyDeclined):
            bus.handle(cmds.AcceptKeep(keep_id=kid, by=uid2))

        # Then
        with bus.uows.get(model.Keep) as uow:
            repo: KeepRepository = uow.repo
            assert repo.all()[0].state == RootAggState.REMOVED