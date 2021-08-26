from pydantic import BaseModel


class Links(BaseModel):
    self: str


class HTTPError(BaseModel):
    """
    HTTP error schema to be used when an `HTTPException` is thrown.
    """

    detail: str
