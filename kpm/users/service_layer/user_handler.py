import os
import random

from jinja2 import Environment, FileSystemLoader

import kpm.users.domain.commands as cmds
import kpm.users.domain.events as events
import kpm.users.domain.model as model
from kpm.shared.adapters.notifications import AbstractNotifications
from kpm.shared.domain.model import RootAggState, UserId
from kpm.shared.log import logger
from kpm.shared.security import generate_salt, hash_password, salt_password
from kpm.shared.service_layer.unit_of_work import AbstractUnitOfWork
from kpm.users.domain.repositories import UserRepository


def _load_email_templates() -> Environment:
    return Environment(
        loader=FileSystemLoader(
            os.path.join(os.path.dirname(__file__), "templates")
        )
    )


def register_user(cmd: cmds.RegisterUser, user_uow: AbstractUnitOfWork):
    salt = generate_salt()
    if len(cmd.password) < 8:
        raise ValueError("Password too short. Minimum 8 is characters.")
    if 96 < len(cmd.password):
        raise ValueError("Password too long. Maximum of 96 allowed.")

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
            user = model.User(
                username=cmd.username,
                salt=salt,
                email=cmd.email,
                password_hash=hash_password(salt_password(cmd.password, salt)),
                id=UserId(cmd.user_id),
                referred_by=cmd.referred_by,
            )
            if repo.exists_email(user.email):
                raise model.EmailAlreadyExistsException()
            if repo.exists_username(user.username):
                raise model.UsernameAlreadyExistsException()
        repo.create(user)
        uow.commit()


def update_password(
    cmd: cmds.UpdateUserPassword, user_uow: AbstractUnitOfWork
):
    if len(cmd.new_password) < 8:
        raise ValueError("Password too short. Minimum 8 is characters.")
    if 96 < len(cmd.new_password):
        raise ValueError("Password too long. Maximum of 96 allowed.")

    with user_uow as uow:
        repo: UserRepository = uow.repo
        user: model.User = repo.get(UserId(cmd.user_id))
        if not user:
            raise model.UserNotFound()
        user.change_password_hash(cmd)
        repo.update(user)
        uow.commit()


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


def send_activation_email(
    event: events.UserActivated, user_uow: AbstractUnitOfWork,
    email_notifications: AbstractNotifications
):
    env = _load_email_templates()
    with user_uow as uow:
        repo: UserRepository = uow.repo
        user: model.User = repo.get(UserId(event.aggregate_id))
        if not user:
            raise model.UserNotFound()

    template = env.get_template("user_activated.html")
    founder_name = random.choice(["Martí", "David", "Jordi"])
    output = template.render(name=user.username, founder_name=founder_name)
    email_notifications.send(user.email, "Your account is ready", output)


def send_new_user_email(
        event: events.UserRegistered, email_notifications: AbstractNotifications
):
    """Sends welcome email to user and activation to board"""
    env = _load_email_templates()

    template = env.get_template("welcome_email.html")
    founder_name = random.choice(["Martí", "David", "Jordi"])
    welcome = template.render(name=event.username, founder_name=founder_name)

    template = env.get_template("new_user_internal.html")
    activation = template.render(
        id=event.aggregate_id,
        username=event.username,
        email=event.email,
        referral=event.referred_by,
    )

    email_notifications.send_multiple([
        {"to": event.username, "subject": "Welcome to Keepem!",
         "body": welcome},
        {"to": "board@keepem.app", "subject": "User requires activation",
         "body": activation},
    ])


def remove_user(cmd: cmds.RemoveUser, user_uow: AbstractUnitOfWork):
    with user_uow as uow:
        repo: UserRepository = uow.repo
        user: model.User = repo.get(UserId(cmd.user_id))
        if not user:
            raise model.UserNotFound()
        user.remove(
            mod_ts=cmd.timestamp,
            reason=cmd.reason,
            by=UserId(id=cmd.deleted_by),
        )
        repo.update(user)
        uow.commit()
