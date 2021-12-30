import dataclasses

import kpm.users.domain.commands as cmds
import kpm.users.domain.events as events
import kpm.users.domain.model as model
from kpm.shared.adapters.notifications import AbstractNotifications
from kpm.shared.domain.model import RootAggState, UserId
from kpm.shared.security import generate_salt, hash_password, salt_password
from kpm.shared.service_layer.unit_of_work import AbstractUnitOfWork
from kpm.users.domain.repositories import UserRepository


def register_user(cmd: cmds.RegisterUser, user_uow: AbstractUnitOfWork):
    salt = generate_salt()

    user = model.User(
        username=cmd.username,
        salt=salt,
        email=cmd.email,
        password_hash=hash_password(salt_password(cmd.password, salt)),
        id=UserId(cmd.user_id),
    )
    with user_uow as uow:
        repo: UserRepository = uow.repo
        if repo.empty():
            user = dataclasses.replace(
                user, state=RootAggState.ACTIVE, roles=["admin"]
            )
        else:
            if repo.exists_email(user.email):
                raise model.EmailAlreadyExistsException()
            if repo.exists_username(user.username):
                raise model.UsernameAlreadyExistsException()
        repo.create(user)
        uow.commit()


def send_welcome_email(
    event: events.UserRegistered, email_notifications: AbstractNotifications
):
    """Sends welcome email"""
    raise NotImplementedError
