from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, validator

from kpm.settings import settings
from kpm.shared.entrypoints.fastapi.schemas import Links


class AssetUpdatableFields(BaseModel):
    """Updatable fields of Asset"""

    title: Optional[str]
    description: Optional[str]
    tags: Optional[List[str]]
    people: Optional[List[str]]
    location: Optional[str]
    created_date: Optional[str]
    """Default value at creation: False"""
    extra_private: Optional[bool] = False
    """Default value at creation: False"""
    bookmarked: Optional[bool] = False


class AssetBase(AssetUpdatableFields):
    title: str
    description: str
    """Optional. If no owners are specified, the calling user is added"""
    owners_id: List[str]
    file_type: str
    file_name: str
    """File size in bytes. Will be double checked but it's needed."""
    file_size_bytes: int


class AssetCreate(AssetBase):
    owners_id: List[str] = None

    @validator("owners_id", always=True)
    def clean_owners_id(cls, v):
        if v:
            return [settings.API_USER_PATH.remove_from(oid) for oid in v]
        else:
            return []


class AssetResponse(AssetBase):
    id: str
    links: Optional[Links]
    upload_path: Optional[str]
    """UNIX timestamp in milliseconds"""
    created_ts: int
    """UNIX timestamp in milliseconds"""
    modified_ts: Optional[int]
    state: str

    @validator("links", always=True)
    def populate_links(cls, _, values):
        return Links(
            self=settings.API_ASSET_PATH.prefix + "/" + values.get("id")
        )

    @validator("owners_id")
    def populate_owners_links(cls, owners_id) -> List[Links]:
        return [settings.API_USER_PATH.prefix + "/" + oid for oid in owners_id]


class AssetUploadAuthData(BaseModel):
    """Data inside asset upload authorizer token"""

    asset_id: str
    user_id: str
