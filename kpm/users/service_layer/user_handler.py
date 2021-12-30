import dataclasses

import kpm.users.domain.commands as cmds
import kpm.users.domain.events as events
import kpm.users.domain.model as model
from kpm.shared.adapters.notifications import AbstractNotifications
from kpm.shared.domain.model import RootAggState, UserId
from kpm.shared.security import generate_salt, hash_password, salt_password
from kpm.shared.service_layer.unit_of_work import AbstractUnitOfWork


def register_user(cmd: cmds.RegisterUser, user_uow: AbstractUnitOfWork):
    salt = generate_salt()

    user = model.User(
        username=cmd.username,
        salt=salt,
        password_hash=hash_password(salt_password(cmd.password, salt)),
        id=UserId(cmd.user_id),
    )
    with user_uow as uow:
        if uow.repo.empty():
            user = dataclasses.replace(
                user, state=RootAggState.ACTIVE, roles=["admin"]
            )

        uow.repo.create(user)
        uow.commit()


def send_welcome_email(
    event: events.UserRegistered, email_notifications: AbstractNotifications
):
    """Sends welcome email"""
    raise NotImplementedError
