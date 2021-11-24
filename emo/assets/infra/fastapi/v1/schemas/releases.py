from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, validator

from emo.settings import settings
from emo.shared.infra.fastapi.schemas import Links


class TransferAssets(BaseModel):
    asset_ids: List[str]
    name: str
    receivers: List[str]
    description: str = None


class CreateAssetToFutureSelf(BaseModel):
    assets: List[str]
    """UNIX timestamp in milliseconds"""
    scheduled_date: int
    name: str
    description: str = None


class CreateAssetInABottle(BaseModel):
    assets: List[str]
    """UNIX timestamp in milliseconds"""
    scheduled_date: int
    name: str
    receivers: List[str]
    description: str = None


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
