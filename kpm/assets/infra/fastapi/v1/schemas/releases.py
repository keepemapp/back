from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, validator

from kpm.settings import settings
from kpm.shared.infra.fastapi.schemas import Links


class TransferBase(BaseModel):
    assets: List[str]
    name: str
    description: str = None

    @validator("assets", always=True)
    def clean_assets(cls, v):
        return settings.API_ASSET_PATH.remove_from(v)


class TransferAssets(TransferBase):
    receivers: List[str]

    @validator("receivers", always=True)
    def clean_users(cls, v):
        return settings.API_USER_PATH.remove_from(v)


class CreateAssetToFutureSelf(TransferBase):
    """UNIX timestamp in milliseconds"""

    scheduled_date: int


class CreateAssetInABottle(TransferAssets):
    """UNIX timestamp in milliseconds"""

    scheduled_date: int
    receivers: List[str]


class ReleaseConditions(BaseModel):

    """When the release wil happen (approx) UTC Unixtime in milliseconds!!!"""

    release_time: int
    """This is incompatible with the others and takes priority."""
    immediate: bool = False


class ReleaseBase(BaseModel):
    release_type: str
    name: str
    description: str
    receivers: List[str]
    assets: List[str]
    conditions: ReleaseConditions
    """UNIX timestamp in milliseconds"""
    created_ts: int
    """UNIX timestamp in milliseconds"""
    modified_ts: Optional[int]


class ReleaseResponse(ReleaseBase):
    owner: str
    id: str
    links: Optional[Links]

    @validator("links", always=True)
    def populate_links(cls, _, values):
        return Links(self=settings.API_RELEASE.prefix + "/" + values.get("id"))

    @validator("receivers")
    def populate_rec_links(cls, receivers):
        return [settings.API_USER_PATH.prefix + "/" + id for id in receivers]

    @validator("owner")
    def populate_owner(cls, owner):
        return settings.API_USER_PATH.prefix + "/" + owner

    @validator("assets")
    def populate_assets_links(cls, assets):
        return [settings.API_ASSET_PATH.prefix + "/" + id for id in assets]
