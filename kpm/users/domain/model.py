import dataclasses
import random
import re
import string
from dataclasses import field
from typing import List, Optional

from pydantic.dataclasses import dataclass

import kpm.users.domain.commands as cmds
from kpm.shared.domain import (
    required_field,
    required_updatable_field,
    updatable_field,
)
from kpm.shared.domain.model import (ValueObject, FINAL_STATES, RootAggState,
                                     RootAggregate,
                                     UserId)
from kpm.shared.log import logger
from kpm.shared.security import hash_password, salt_password, verify_password
from kpm.users.domain import events
from kpm.users.domain.events import UserReminderAdded, UserReminderRemoved

INVALID_USERNAME = (
    "Username is not valid. It can contain letters, "
    "numbers and underscores and have between "
    "2 and 15 characters."
)
INVALID_EMAIL = "Email is not valid"


def generate_referral_code() -> str:
    chars = string.ascii_letters + string.digits
    # Avoid ambiguous characters
    chars = (
        chars.replace("l", "")
        .replace("I", "")
        .replace("1", "")
        .replace("O", "")
        .replace("0", "")
        .replace("S", "")
        .replace("5", "")
    )
    candidate = "".join(random.choice(chars) for x in range(5))
    forbidden_words = ["nazis", "nigga"]
    if candidate.lower() in forbidden_words:
        return generate_referral_code()
    else:
        return candidate


@dataclass(frozen=True)
class Reminder(ValueObject):
    title: str = required_field()  # type: ignore
    time: int = required_field()  # type: ignore
    frequency: int = field(default=0)
    related_user: Optional[UserId] = updatable_field(default=None)  # type: ignore

    def __hash__(self):
        return hash(self.title) + hash(self.time)

    def __eq__(self, other) -> bool:
        return type(self) == type(other) and self.__hash__() == other.__hash__()


@dataclass
class User(RootAggregate):
    id: UserId = required_field()  # type: ignore
    username: str = required_updatable_field()  # type: ignore
    """Name to be shown to other users"""
    public_name: Optional[str] = updatable_field(default=None)  # type: ignore
    salt: str = field(default="", repr=False)
    password_hash: str = field(default="", repr=False)
    email: str = required_updatable_field()  # type: ignore
    state: RootAggState = field(default=RootAggState.PENDING)
    roles: List[str] = field(default_factory=lambda: ["user"])
    referral_code: str = field(default_factory=generate_referral_code)
    referred_by: Optional[str] = field(default=None)
    removed_by: Optional[UserId] = updatable_field(default=None)
    removed_reason: Optional[str] = updatable_field(default=None)
    reminders: List[Reminder] = updatable_field(default_factory=list)

    @staticmethod
    def _email_is_valid(email: str) -> bool:
        regex = r"^[a-z0-9+\._-]+[@][.\w]+?[.]\w{2,10}$"
        return True if re.match(regex, email) else False

    @staticmethod
    def _name_is_valid(name: str) -> bool:
        regex = r"^[a-z_0-9]{2,15}$"
        return True if re.match(regex, name) else False

    def __post_init__(self, loaded_from_db: bool):
        self.username = self.username.lower().strip()
        self.email = self.email.lower().strip()
        self._id_type_is_valid(UserId)
        if not self._name_is_valid(self.username):
            raise ValueError(INVALID_USERNAME)
        if not self._email_is_valid(self.email):
            raise ValueError(INVALID_EMAIL)

        if not loaded_from_db:
            self.events.append(
                events.UserRegistered(
                    aggregate_id=self.id.id,
                    username=self.username,
                    email=self.email,
                    referred_by=self.referred_by,
                )
            )

    def activate(self, mod_ts: int = None):
        is_updated = self._update_field(mod_ts, "state", RootAggState.ACTIVE)
        if is_updated:
            self.events.append(events.UserActivated(aggregate_id=self.id.id))

    def disable(self, mod_ts: int = None):
        if self.state not in FINAL_STATES:
            self._update_field(mod_ts, "state", RootAggState.INACTIVE)

    def remove(self, mod_ts: Optional[int] = None, **kwargs):
        if self.state != RootAggState.REMOVED:
            by = kwargs.get("by")
            if isinstance(by, str):
                by = UserId(id=by)
            reason = kwargs.get("reason")
            if by is None or reason is None:
                raise ValueError("'by' and 'reason' must be set")
            self.update_fields(
                mod_ts,
                {
                    "removed_by": by,
                    "removed_reason": reason,
                    "email": f"{self.id.id}@removed.keepem.app".lower(),
                    "public_name": None,
                },
            )
            self.events.append(
                events.UserRemoved(
                    aggregate_id=self.id.id, by=by.id, reason=reason
                )
            )
            self._update_field(mod_ts, "state", RootAggState.REMOVED)

    def is_disabled(self) -> bool:
        return self.state not in [RootAggState.ACTIVE]

    def is_pending_validation(self):
        return self.state in [RootAggState.PENDING]

    def erase_sensitive_data(self) -> "User":
        return dataclasses.replace(self, salt="", password_hash="")

    def change_password_hash(self, cmd: cmds.UpdateUserPassword):
        self.validate_password(cmd.old_password)

        new_pwd = hash_password(salt_password(cmd.new_password, self.salt))
        logger.info(
            f"Password updated for user '{self.id.id}'", component="auth"
        )
        self._update_field(
            mod_ts=cmd.timestamp, field="password_hash", value=new_pwd
        )

    def validate_password(self, password: str):
        salted_pwd = salt_password(password, self.salt)
        pwd_valid = verify_password(salted_pwd, self.password_hash)
        if not pwd_valid:
            logger.info(
                f"Password auth failure for user '{self.id.id}'",
                component="auth",
            )
            raise MissmatchPasswordException()
        logger.info(
            f"Password auth success for user '{self.id.id}'", component="auth"
        )

    def add_reminder(self, reminder: Reminder, mod_ts: int):
        original_reminders = self.reminders
        if not original_reminders:
            original_reminders = []
        updated = []
        removed = []
        for r in [reminder] + original_reminders:
            if r not in updated:
                updated.append(r)
            else:
                removed.append(r)

        self.update_fields(mod_ts=mod_ts, updates={"reminders": updated})
        for r in removed:
            self.events.append(
                UserReminderRemoved(
                    aggregate_id=self.id.id,
                    title=r.title,
                    time=r.time,
                    timestamp=mod_ts - 1
                ))

        self.events.append(
            UserReminderAdded(
                aggregate_id=self.id.id,
                title=reminder.title,
                time=reminder.time,
                frequency=reminder.frequency,
                related_user=reminder.related_user.id if reminder.related_user else None,
                timestamp=mod_ts
            ))

    def remove_reminder(self, reminder: Reminder, mod_ts: int):
        if not self.reminders:
            return
        updated = [r for r in self.reminders if r is not reminder]
        self.update_fields(mod_ts=mod_ts, updates={"reminders": updated})

        self.events.append(
            UserReminderRemoved(
                aggregate_id=self.id.id,
                title=reminder.title,
                time=reminder.time,
                timestamp=mod_ts - 1
            ))

    def __hash__(self):
        return hash(self.id.id)


class MissmatchPasswordException(Exception):
    def __init__(self, msg="Passwords do not match"):
        self.msg = msg


class EmailAlreadyExistsException(Exception):
    def __init__(self, msg="Email already exists"):
        self.msg = msg


class UserNotFound(KeyError):
    def __init__(self, msg="User not found"):
        self.msg = msg


class UsernameAlreadyExistsException(Exception):
    def __init__(self, msg="Username already exists"):
        self.msg = msg


@dataclass
class Keep(RootAggregate):
    requester: UserId = required_field()  # type: ignore
    requested: UserId = required_field()  # type: ignore
    name_by_requester: Optional[str] = None
    name_by_requested: Optional[str] = None
    declined_by: Optional[str] = None
    declined_reason: Optional[str] = None
    state: RootAggState = field(default=RootAggState.PENDING)

    def __post_init__(self, loaded_from_db: bool):
        if self.state == RootAggState.PENDING:
            if not loaded_from_db:
                self.events.append(
                    events.KeepRequested(
                        aggregate_id=self.id.id,
                        requester=self.requester.id,
                        requested=self.requested.id,
                    )
                )

    def accept(self, name_by_requested: str = None, mod_ts: int = None):
        if self.state != RootAggState.PENDING:
            if self.state == RootAggState.ACTIVE:
                return
            else:
                raise KeepAlreadyDeclined()

        self._update_field(mod_ts, "name_by_requested", name_by_requested)
        is_updated = self._update_field(mod_ts, "state", RootAggState.ACTIVE)
        if is_updated:
            self.events.append(
                events.KeepAccepted(
                    aggregate_id=self.id.id,
                    requester=self.requester.id,
                    requested=self.requested.id,
                )
            )

    def decline(self, by_id: UserId, reason: str = "", mod_ts: int = None):
        if by_id == self.requester:
            declined_by_value = "requester"
        elif by_id == self.requested:
            declined_by_value = "requested"
        else:
            raise ValueError("User declining it is not part of this keep.")

        was_accepted = self.state == RootAggState.ACTIVE
        is_updated = self.update_fields(
            mod_ts,
            {
                "state": RootAggState.REMOVED,
                "declined_by": declined_by_value,
                "declined_reason": reason,
            },
            allow_all=True,
        )
        if is_updated:
            self.events.append(
                events.KeepDeclined(
                    aggregate_id=self.id.id,
                    was_accepted=was_accepted,
                    requester=self.requester.id,
                    requested=self.requested.id,
                )
            )

    def __hash__(self):
        return hash(self.id.id)


@dataclass
class Session(RootAggregate):
    user: UserId = required_field()  # type: ignore
    # client ID / device ID (used for sending push notifications if applies)
    client_id: Optional[str] = None  # type: ignore
    refresh_token: str = required_field()  # type: ignore
    state: RootAggState = field(default=RootAggState.ACTIVE)
    removed_by: Optional[str] = updatable_field()  # type: ignore

    def remove(self, mod_ts: Optional[int], by_id: UserId = None, **kwargs):
        if self.state != FINAL_STATES:
            self.update_fields(mod_ts, {"removed_by": by_id.id})
            self._update_field(mod_ts, "state", RootAggState.REMOVED)

    def __hash__(self):
        return hash(self.id.id)


class DuplicatedKeepException(Exception):
    def __init__(self, msg="This keep was already created"):
        self.msg = msg


class KeepAlreadyDeclined(Exception):
    def __init__(self, msg="This keep was already declined"):
        self.msg = msg


class KeepActionError(Exception):
    def __init__(self, msg="Error acting on a keep"):
        self.msg = msg


class ValidationPending(Exception):
    def __init__(self, msg="User pending validation"):
        self.msg = msg


class InvalidSession(Exception):
    def __init__(self, msg="Session has expired or was invalidated"):
        self.msg = msg


class InvalidScope(Exception):
    pass
