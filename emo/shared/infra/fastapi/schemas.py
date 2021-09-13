from pydantic import BaseModel


class Links(BaseModel):
    self: str


class HTTPError(BaseModel):
    """
    HTTP error schema to be used when an `HTTPException` is thrown.
    """

    detail: str


class TokenData(BaseModel):
    """Data inside the token.

    It needs to be enough for all microservices so they do not need to ask
    for extra user information. Include auth groups, ids...
    """

    user_id: str
    disabled: bool
