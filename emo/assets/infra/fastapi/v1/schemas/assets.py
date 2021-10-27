from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, validator

from emo.settings import settings
from emo.shared.infra.fastapi.schemas import Links


class AssetBase(BaseModel):
    title: str
    description: str
    owners_id: List[str]
    file_type: str
    file_name: str


class AssetCreate(AssetBase):
    pass


class AssetResponse(AssetBase):
    id: str
    links: Optional[Links]
    upload_path: Optional[str]

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
