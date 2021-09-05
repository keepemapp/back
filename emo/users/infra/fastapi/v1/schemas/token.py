from pydantic import BaseModel

from emo.shared.domain import UserId


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: UserId
