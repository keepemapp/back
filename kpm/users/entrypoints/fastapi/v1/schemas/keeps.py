from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, validator, root_validator

from kpm.settings import settings as s
from kpm.shared.entrypoints.fastapi.schemas import Links


class KeepResponse(BaseModel):
    id: str
    """UNIX timestamp in milliseconds"""
    created_ts: int
    """UNIX timestamp in milliseconds"""
    modified_ts: Optional[int]
    state: str
    requester: str
    requested: str
    declined_by: Optional[str] = None

    @validator("requester")
    def populate_requester(cls, uid: str) -> Links:
        return s.API_USER_PATH.concat(uid).path()

    @validator("requested")
    def populate_requested(cls, uid: str) -> Links:
        return s.API_USER_PATH.concat(uid).path()


class RequestKeep(BaseModel):
    """"Friend" (keep) request by user ID or code.
    Just one at the same time is accepted
    """

    to_id: Optional[str] = None
    """User's referral code"""
    to_code: Optional[str] = None

    @validator("to_id", always=True)
    def clean_to_id(cls, v):
        if v:
            return s.API_USER_PATH.remove_from(v)
        return v

    @root_validator
    def only_one_set(cls, values):
        id, code = values.get('to_id'), values.get("to_code")
        if id is not None and code is not None:
            raise ValueError("Just one value can be set at the same time.")
        elif id is None and code is None:
            raise ValueError("Unset values")
        else:
            return values


class AcceptKeep(BaseModel):
    keep_id: str


class DeclineKeep(BaseModel):
    keep_id: str
    reason: str
