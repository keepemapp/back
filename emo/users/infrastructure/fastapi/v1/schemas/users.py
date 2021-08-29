from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, validator

from emo.settings import settings
from emo.shared.infrastructure.fastapi.schemas import Links


class UserBase(BaseModel):
    username: str
    email: Optional[str]


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: str
    password: str


# Additional properties to return via API
class UserResponse(UserBase):
    id: str
    links: Optional[Links]

    @validator("links")
    def populate_links(cls, v, values):
        return Links(
            self=settings.API_USER_PATH.prefix + "/" + values.get("id")
        )


# Properties to receive via API on update
class PasswordUpdate(UserBase):
    password: Optional[str] = None
