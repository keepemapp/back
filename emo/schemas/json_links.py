from typing import Optional, List
from pydantic import BaseModel, validator

from api import settings


class UserLink(BaseModel):
    id: str
    self: Optional[str] = None

    @validator('self', always=True)
    def set_self(cls, v, values) -> str:
        return f"{settings.API_USER_PATH}/{values['id']}"


class AssetLink(BaseModel):
    id: str
    self: Optional[str] = None

    @validator('self', always=True)
    def set_self(cls, v, values) -> str:
        return f"{settings.API_ASSET_PATH}/{values['id']}"


class TransferLink(BaseModel):
    id: str
    self: Optional[str] = None

    @validator('self', always=True)
    def set_self(cls, v, values) -> str:
        return f"{settings.API_TRANSFER_PATH}/{values['id']}"