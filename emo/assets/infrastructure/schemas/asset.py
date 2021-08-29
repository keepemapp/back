from typing import Optional

from pydantic import BaseModel, validator

from emo.schemas import AssetLink, UserLink


# Shared properties
class AssetBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    type: str
    file_name: str


# Properties to receive on item creation
class AssetCreate(AssetBase):
    title: str
    type: str
    file_name: str


# Properties to receive on item update
class AssetUpdate(AssetBase):
    pass


# Properties shared by models stored in DB
class AssetInDBBase(AssetBase):
    id: str
    title: str
    owner_id: str


# Properties to return to client
class Asset(AssetInDBBase):
    id: str
    owner_id: str
    self: Optional[AssetLink] = None
    owner: Optional[UserLink] = None

    @validator("self", always=True)
    def set_self(cls, v, values) -> AssetLink:
        return AssetLink(id=values["id"])

    @validator("owner", always=True)
    def set_owner(cls, v, values) -> UserLink:
        return UserLink(id=values["owner_id"])


# Properties properties stored in DB
class AssetInDB(AssetInDBBase):
    pass
