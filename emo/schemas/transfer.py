from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, validator

from api import settings
from emo.schemas import UserLink, AssetLink, TransferLink

# Shared properties
class TransferBase(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_date: datetime
    assets_ids: List[str]
    transferor_id: str
    receiver_ids: List[str]


# Properties to receive on item creation
class TransferCreate(TransferBase):
    title: str
    scheduled_date: datetime
    assets_ids: List[str]
    transferer_id: str
    receiver_ids: List[str]


# Properties to receive on item update
class TransferUpdate(TransferBase):
    pass


# Properties shared by models stored in DB
class TransferInDBBase(TransferBase):
    id: str


# Properties to return to client
class Transfer(TransferInDBBase):
    id: str
    assets_ids: List[str]
    transferor_id: str
    receiver_ids: List[str]

    assets: Optional[List[AssetLink]] = None
    transferor: Optional[UserLink] = None
    receivers: Optional[List[UserLink]] = None

    @validator('assets', always=True)
    def set_assets(cls, v, values) -> List[AssetLink]:
        return [AssetLink(id=a) for a in values['assets_ids']]

    @validator('transferor', always=True)
    def set_transferor(cls, v, values) -> UserLink:
        return UserLink(id=values['transferor_id'])

    @validator('receivers', always=True)
    def set_receivers(cls, v, values) -> List[UserLink]:
        return [UserLink(id=a) for a in values['receiver_ids']]


# Properties properties stored in DB
class TransferInDB(TransferInDBBase):
    pass
