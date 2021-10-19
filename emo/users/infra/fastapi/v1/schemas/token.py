from pydantic import BaseModel


class LoginResponse(BaseModel):
    user_id: str
    access_token: str
    token_type: str
