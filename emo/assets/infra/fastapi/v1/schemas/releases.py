from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, validator, dataclasses

from emo.assets.domain.usecase import asset_in_a_bottle as b
from emo.assets.domain.usecase import asset_to_future_self as afs
from emo.assets.domain.usecase import stash as st
from emo.assets.domain.usecase import time_capsule as tc
from emo.assets.domain.usecase import transfer as tr
from emo.settings import settings
from emo.shared.infra.fastapi.schemas import Links

CreateAssetToFutureSelf = dataclasses.dataclass(afs.CreateAssetToFutureSelf)
CreateAssetInABottle = dataclasses.dataclass(b.CreateAssetInABottle)
CreateStash = dataclasses.dataclass(st.Stash)
CreateTimeCapsule = dataclasses.dataclass(tc.CreateTimeCapsule)
TransferAssets = dataclasses.dataclass(tr.TransferAssets)


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
        return Links(
            self=settings.API_RELEASE_PATH.prefix + "/" + values.get("id")
        )

    @validator("receivers")
    def populate_rec_links(cls, receivers):
        return [settings.API_USER_PATH.prefix + "/" + id for id in receivers]

    @validator("owner")
    def populate_owner(cls, owner):
        return settings.API_USER_PATH.prefix + "/" + owner

    @validator("assets")
    def populate_assets_links(cls, assets):
        return [settings.API_ASSET_PATH.prefix + "/" + id for id in assets]

