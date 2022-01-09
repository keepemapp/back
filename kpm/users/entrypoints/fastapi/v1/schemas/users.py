from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, validator

from kpm.settings import settings
from kpm.shared.entrypoints.fastapi.schemas import Links


class UserBase(BaseModel):
    username: str
    email: Optional[str]
    public_name: Optional[str]


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: str
    password: str


# Additional properties to return via API
class UserResponse(UserBase):
    id: str
    state: str
    roles: List[str]
    links: Optional[Links]

    @validator("links", always=True)
    def populate_links(cls, _, values):
        return Links(
            self=settings.API_USER_PATH.prefix + "/" + values.get("id")
        )


class UserPublic(BaseModel):
    id: str
    public_name: Optional[str]
    links: Optional[Links]

    @validator("links", always=True)
    def populate_links(cls, _, values):
        return Links(
            self=settings.API_USER_PATH.prefix + "/" + values.get("id")
        )


# Properties to receive via API on update
class PasswordUpdate(BaseModel):
    old_password: Optional[str] = None
    new_password: Optional[str] = None


# Properties to receive via API on update
class UserUpdate(BaseModel):
    public_name: Optional[str]
