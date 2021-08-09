from pydantic import BaseSettings


class Settings(BaseSettings):
    APPLICATION_NAME: str = "My Heritage"
    APPLICATION_TECHNICAL_NAME: str = "my_heritage"

    API_V1_STR: str = "/api/v1"

    API_ASSET_PATH: str = "/asset"
    API_TRANSFER_PATH: str = "/transfer"
    API_USER_PATH: str = "/user"


settings = Settings()
