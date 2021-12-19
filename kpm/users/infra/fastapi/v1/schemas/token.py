from pydantic import BaseModel


class LoginResponse(BaseModel):
    user_id: str
    access_token: str
    """Number of seconds the access token will be valid for"""
    access_token_expires: int
    refresh_token: str
    refresh_token_expires: int
