from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, validator

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
    to_user: str

    @validator("to_user", always=True)
    def clean_to_user(cls, v):
        return s.API_USER_PATH.remove_from(v)


class AcceptKeep(BaseModel):
    keep_id: str


class DeclineKeep(BaseModel):
    keep_id: str
    reason: str
