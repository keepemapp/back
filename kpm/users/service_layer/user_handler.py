import os

from jinja2 import Environment, FileSystemLoader

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

    with user_uow as uow:
        repo: UserRepository = uow.repo
        if repo.empty():
            user = model.User(
                username=cmd.username,
                salt=salt,
                email=cmd.email,
                password_hash=hash_password(salt_password(cmd.password, salt)),
                id=UserId(cmd.user_id),
                state=RootAggState.ACTIVE,
                roles=["admin"],
                referred_by=cmd.referred_by,
            )
        else:
            if repo.exists_email(cmd.email):
                raise model.EmailAlreadyExistsException()
            if repo.exists_username(cmd.username):
                raise model.UsernameAlreadyExistsException()
            user = model.User(
                username=cmd.username,
                salt=salt,
                email=cmd.email,
                password_hash=hash_password(salt_password(cmd.password, salt)),
                id=UserId(cmd.user_id),
                referred_by=cmd.referred_by,
            )
        repo.create(user)
        uow.commit()


def update_password(
    cmd: cmds.UpdateUserPassword, user_uow: AbstractUnitOfWork
):
    with user_uow as uow:
        repo: UserRepository = uow.repo
        user: model.User = repo.get(UserId(cmd.user_id))
        if not user:
            raise model.UserNotFound()
        user.change_password_hash(cmd)
        repo.update(user)
        uow.commit()

    with user_uow as uow:
        repo: UserRepository = uow.repo
        user: model.User = repo.get(UserId(cmd.user_id))


def update_user_attributes(cmd: cmds.UpdateUser, user_uow: AbstractUnitOfWork):
    with user_uow as uow:
        repo: UserRepository = uow.repo
        user: model.User = repo.get(UserId(cmd.user_id))
        if not user:
            raise model.UserNotFound()
        user.update_fields(mod_ts=cmd.timestamp, updates=cmd.update_dict())
        repo.update(user)
        uow.commit()


def activate(cmd: cmds.ActivateUser, user_uow: AbstractUnitOfWork):
    with user_uow as uow:
        repo: UserRepository = uow.repo
        user: model.User = repo.get(UserId(cmd.user_id))
        if not user:
            raise model.UserNotFound()
        user.activate()
        repo.update(user)
        uow.commit()


def send_welcome_email(
    event: events.UserRegistered, email_notifications: AbstractNotifications
):
    """Sends welcome email"""
    env = Environment(
        loader=FileSystemLoader(
            os.path.join(os.path.dirname(__file__), "templates")
        )
    )

    template = env.get_template("welcome_email.html")
    output = template.render(name=event.username)

    email_notifications.send(event.email, "Welcome to Keepem!", output)
