from dataclasses import asdict, field
from datetime import timedelta
from functools import lru_cache
from os import path
from typing import List, Optional, Union

from pydantic import BaseSettings
from pydantic.dataclasses import dataclass


@dataclass
class ApiRoute:
    prefix: str
    tags: List[str] = field(default_factory=list)

    def dict(self):
        return asdict(self)

    def concat(self, *others: Union["ApiRoute", str]) -> "ApiRoute":
        res = self
        for o in others:
            if isinstance(o, ApiRoute):
                res = ApiRoute(
                    prefix=res.prefix + o.prefix, tags=res.tags + o.tags
                )
            else:
                res = ApiRoute(prefix=res.prefix + "/" + o, tags=res.tags)
        return res

    def __str__(self) -> str:
        return self.path()

    def path(self) -> str:
        return ("/" + self.prefix).replace("//", "/")

    def remove_from(self, id_with_path):
        """Removes API path information from the passed parameter"""
        if isinstance(id_with_path, list):
            return [
                s.replace(self.prefix, "").replace("/", "")
                for s in id_with_path
            ]
        else:
            return id_with_path.replace(self.prefix, "").replace("/", "")


class Settings(BaseSettings):
    LOG_LEVEL: str = "DEBUG"
    APPLICATION_NAME: str = "Keepem"
    APPLICATION_TECHNICAL_NAME: str = "Keepem"

    API_V1: ApiRoute = ApiRoute(prefix="/api/v1")
    API_HEALTH: ApiRoute = ApiRoute(prefix="/health")
    API_VERSION: ApiRoute = ApiRoute(prefix="/version")

    API_ME: ApiRoute = ApiRoute(prefix="/me")
    API_TOKEN: ApiRoute = ApiRoute(prefix="/token", tags=["authentication"])
    API_ASSET_PATH: ApiRoute = ApiRoute(prefix="/assets", tags=["assets"])
    API_USER_PATH: ApiRoute = ApiRoute(prefix="/users", tags=["users"])
    API_KEEP_PATH: ApiRoute = ApiRoute(prefix="/me/keeps", tags=["users"])
    API_FEEDBACK: ApiRoute = ApiRoute(prefix="/feedback")

    API_LEGACY: ApiRoute = ApiRoute(
        prefix="/legacy", tags=["legacy_operations"]
    )
    API_ASSET_BOTTLE: ApiRoute = ApiRoute("/in-a-bottle")
    API_FUTURE_SELF = ApiRoute("/to-future-self")
    API_HIDE = ApiRoute("/hide-and-seek")
    API_TRANSFER = ApiRoute("/transfer")
    API_TIME_CAPSULE = ApiRoute("/time-capsule")

    UPLOAD_AUTH_TOKEN_EXPIRE_SEC: int = 30

    JWT_ACCESS_EXPIRE_TIME: timedelta = timedelta(minutes=15)
    JWT_REFRESH_EXPIRE_TIME: timedelta = timedelta(days=60)
    # openssl rand -hex 32
    JWT_SECRET_KEY = (
        "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    )
    JWT_DECODE_ALGORITHMS: set = {"HS384", "HS512"}
    JWT_ALGORITHM = "HS384"

    DATA_FOLDER = path.join(
        path.dirname(path.dirname(path.abspath(__file__))), "data"
    )

    EMAIL_SENDER_ADDRESS: Optional[str]
    """Base64 encoded password"""
    EMAIL_SENDER_PASSWORD: Optional[str]
    EMAIL_SMTP_SERVER: Optional[str]
    EMAIL_SMTP_PORT: int = 587
    EMAIL_SMTP_SECURITY: str = "STARTTLS"

    MONGODB_URL: Optional[str] = "mongodb://127.0.0.1:27017/?replicaSet=rs0"
    MONGODB_USER: Optional[str] = ""
    MONGODB_PWD: Optional[str] = ""

    ASSET_S3_URL: str = "https://eu2.contabostorage.com"
    ASSET_S3_BUCKET: Optional[str] = "kpm-dev"
    ASSET_S3_ACCESS: Optional[str]
    ASSET_S3_SECRET: Optional[str]

    DATA_KEY_ENCRYPTION_KEY: Optional[str]
    ENVIRONMENT: str = "dev"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings():
    res = Settings()
    if res.ASSET_S3_BUCKET and res.ENVIRONMENT != "prod" \
            and res.ENVIRONMENT not in res.ASSET_S3_BUCKET:
        raise ValueError("ENVIRONMENT must be in ASSET_S3_BUCKET")
    return Settings()


settings = get_settings()
