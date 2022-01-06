from __future__ import annotations

import dataclasses
import re
from dataclasses import dataclass, field
from typing import List, Optional

from kpm.shared.domain import required_field
from kpm.shared.domain.model import RootAggregate, RootAggState, UserId
from kpm.users.domain import events

INVALID_USERNAME = (
    "Username is not valid. It can contain letters, "
    "numbers and underscores and have between "
    "2 and 15 characters."
)
INVALID_EMAIL = "Email is not valid"


@dataclass
class User(RootAggregate):
    id: UserId = required_field()
    username: str = required_field()
    salt: str = field(default="", repr=False)
    password_hash: str = field(default="", repr=False)
    email: str = required_field()
    state: RootAggState = field(default=RootAggState.PENDING)
    roles: List[str] = field(default_factory=lambda: ["user"])

    @staticmethod
    def _email_is_valid(email: str) -> bool:
        regex = r"^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,5}$"
        return True if re.match(regex, email) else False

    @staticmethod
    def _name_is_valid(name: str) -> bool:
        regex = r"^[a-z_0-9]{2,15}$"
        return True if re.match(regex, name) else False

    def __post_init__(self):
        self._id_type_is_valid(UserId)
        if not self._name_is_valid(self.username):
            raise ValueError(INVALID_USERNAME)
        if not self._email_is_valid(self.email):
            raise ValueError(INVALID_EMAIL)
        self.events.append(
            events.UserRegistered(
                aggregate_id=self.id.id,
                username=self.username,
                email=self.email,
            )
        )

    def activate(self, mod_ts: int = None):
        is_updated = self._update_field(mod_ts, "state", RootAggState.ACTIVE)
        if is_updated:
            self.events.append(
                events.UserActivated(aggregate_id=self.id.id)
            )

    def disable(self, mod_ts: int = None):
        self._update_field(mod_ts, "state", RootAggState.INACTIVE)

    def is_disabled(self) -> bool:
        return self.state not in [RootAggState.ACTIVE]

    def is_pending_validation(self):
        return self.state in [RootAggState.PENDING]

    def erase_sensitive_data(self) -> User:
        return dataclasses.replace(self, salt="", password_hash="")

    def change_password_hash(self, new_password_hash):
        return dataclasses.replace(self, password_hash=new_password_hash)

    def __hash__(self):
        return hash(self.id.id)


class MissmatchPasswordException(Exception):
    def __init__(self, msg="Passwords do not match"):
        self.msg = msg


class EmailAlreadyExistsException(Exception):
    def __init__(self, msg="Email already exists"):
        self.msg = msg


class UsernameAlreadyExistsException(Exception):
    def __init__(self, msg="Username already exists"):
        self.msg = msg


@dataclass
class Keep(RootAggregate):
    requester: UserId = required_field()
    requested: UserId = required_field()
    name_by_requester: str = required_field()
    name_by_requested: Optional[str] = None
    declined_by: Optional[str] = None
    declined_reason: Optional[str] = None
    state: RootAggState = field(default=RootAggState.PENDING)

    def __post_init__(self):
        if self.state == RootAggState.PENDING:
            self.events.append(
                events.KeepRequested(
                    aggregate_id=self.id.id,
                    requester=self.requester.id,
                    requested=self.requested.id,
                )
            )

    def accept(self, name_by_requested: str, mod_ts: int = None):
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
        is_updated = self._update_field(mod_ts, "state", RootAggState.REMOVED)
        if is_updated:
            self._update_field(mod_ts, "declined_by", declined_by_value)
            self._update_field(mod_ts, "declined_reason", reason)
            self.events.append(
                events.KeepDeclined(
                    aggregate_id=self.id.id,
                    was_accepted=was_accepted,
                    requester=self.requester.id,
                    requested=self.requested.id,
                )
            )


class DuplicatedKeepException(Exception):
    def __init__(self, msg="This keep was already created"):
        self.msg = msg


class KeepAlreadyDeclined(Exception):
    def __init__(self, msg="This keep was already declined"):
        self.msg = msg


class KeepActionError(Exception):
    def __init__(self, msg="Error acting on a keep"):
        self.msg = msg