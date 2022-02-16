from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, validator

from kpm.settings import settings
from kpm.shared.entrypoints.fastapi.schemas import Links


class LegacyOperationBase(BaseModel):
    """Base mixin adding common Legacy Operation properties"""

    assets: List[str]
    name: str
    description: str = None

    @validator("assets", always=True)
    def clean_assets(cls, v):
        return settings.API_ASSET_PATH.remove_from(v)


class _Receivers(BaseModel):
    """Base mixin adding receivers list"""

    receivers: List[str]

    @validator("receivers", always=True)
    def clean_users(cls, v):
        return settings.API_USER_PATH.remove_from(v)


class _GeographicalCondition(BaseModel):
    """Base mixin adding scheduled date in ms"""

    """UNIX timestamp in milliseconds"""
    scheduled_date: int


class CreateTransfer(LegacyOperationBase, _Receivers):
    """Structure to create an assets transfer legacy operation"""

    """UNIX timestamp in milliseconds"""
    scheduled_date: Optional[int] = None


class CreateAssetToFutureSelf(LegacyOperationBase):
    """Structure to create an asset to future self legacy operation"""

    """UNIX timestamp in milliseconds"""
    scheduled_date: int


class CreateAssetInABottle(LegacyOperationBase, _Receivers):
    """Structure to create an asset in a bottle legacy operation.

    Default min is 1 month from now and default max is 1 year from now.
    """

    """UNIX timestamp in milliseconds. If none, a random will be chosen."""
    min_date: Optional[int] = None
    """UNIX timestamp in milliseconds. If none, a random will be chosen."""
    max_date: Optional[int] = None

    @validator("max_date", always=True)
    def validate_min_max(cls, field_value, values):
        if not field_value and values["min_date"]:
            raise ValueError("Both min_date and max_date must be set")
        if field_value:
            if not values["min_date"]:
                raise ValueError("Both min_date and max_date must be set")
            if field_value < values["min_date"]:
                raise ValueError("Mix and Max dates are swapped")
        return field_value


class ReleaseConditions(BaseModel):

    """When the release wil happen (approx) UTC Unixtime in milliseconds!!!"""

    release_time: int
    """This is incompatible with the others and takes priority."""
    immediate: bool = False


class ReleaseTrigger(BaseModel):
    aggregate_id: str
    """Optional field for the geographical conditions.
    Compares lowercase and without spaces"""
    geo_location: str = None


class ReleaseBase(BaseModel):
    release_type: str
    receivers: List[str]
    # conditions: ReleaseConditions
    """UNIX timestamp in milliseconds"""
    created_ts: int
    """UNIX timestamp in milliseconds"""
    modified_ts: Optional[int]
    description: str = None
    state: str = None


class ReleaseResponse(ReleaseBase):
    owner: str
    id: str
    links: Optional[Links]
    release_type: str
    name: str
    receivers: List[str]
    assets: List[str]
    # conditions: ReleaseConditions
    """UNIX timestamp in milliseconds"""
    created_ts: int
    """UNIX timestamp in milliseconds"""
    modified_ts: Optional[int]
    description: Optional[str]
    state: Optional[str]

    @validator("links", always=True)
    def populate_links(cls, _, values):
        return Links(self=settings.API_LEGACY.prefix + "/" + values.get("id"))

    @validator("receivers")
    def populate_rec_links(cls, receivers):
        return [settings.API_USER_PATH.prefix + "/" + id for id in receivers]

    @validator("owner")
    def populate_owner(cls, owner):
        return settings.API_USER_PATH.prefix + "/" + owner

    @validator("assets")
    def populate_assets_links(cls, assets):
        return [settings.API_ASSET_PATH.prefix + "/" + id for id in assets]
