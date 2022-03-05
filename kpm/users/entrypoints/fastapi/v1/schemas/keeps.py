from typing import Optional

from pydantic import BaseModel, root_validator, validator

from kpm.settings import settings as s
from kpm.users.entrypoints.fastapi.v1.schemas.users import UserPublic


class KeepResponse(BaseModel):
    id: str
    """UNIX timestamp in milliseconds"""
    created_ts: int
    """UNIX timestamp in milliseconds"""
    modified_ts: Optional[int]
    state: str
    requester: UserPublic
    requested: UserPublic
    declined_by: Optional[str] = None


class RequestKeep(BaseModel):
    """ "Friend" (keep) request by user ID or code.
    Just one at the same time is accepted
    """

    to_id: Optional[str] = None
    """User's referral code"""
    to_code: Optional[str] = None
    to_email: Optional[str] = None

    @validator("to_id", always=True)
    def clean_to_id(cls, v):
        if v:
            return s.API_USER_PATH.remove_from(v)
        return v

    @root_validator
    def only_one_set(cls, values):
        id, code = values.get("to_id"), values.get("to_code")
        email = values.get("to_email")
        num_set = len([v for v in [id, code, email] if v])
        if num_set > 1:
            raise ValueError("Just one value can be set at the same time.")
        elif num_set == 0:
            raise ValueError("Unset values")
        else:
            return values

    class Config:
        schema_extra = {
            "example": {
                "to_code": "skwe8c",
            }
        }


class AcceptKeep(BaseModel):
    keep_id: str


class DeclineKeep(BaseModel):
    keep_id: str
    reason: str
