from pydantic import BaseSettings


class Settings(BaseSettings):
    APPLICATION_NAME: str = "My Heritage"
    APPLICATION_TECHNICAL_NAME: str = "my_heritage"

    API_V1_STR: str = "/api/v1"

    API_ASSET_PATH: str = "/assets"
    API_TRANSFER_PATH: str = "/transfers"
    API_USER_PATH: str = "/users"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM = "HS256"


settings = Settings()
