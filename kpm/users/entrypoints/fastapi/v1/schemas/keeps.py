from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, validator

from kpm.settings import settings
from kpm.shared.entrypoints.fastapi.schemas import Links


class RequestKeep(BaseModel):
    to_user: str

    @validator("to_user", always=True)
    def clean_to_user(cls, v):
        return settings.API_USER_PATH.remove_from(v)


class AcceptKeep(BaseModel):
    keep_id: str


class DeclineKeep(BaseModel):
    keep_id: str
    reason: str
