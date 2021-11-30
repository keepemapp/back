from __future__ import annotations

from dataclasses import asdict, dataclass, field
from os import path
from typing import Dict, List, Union

from pydantic import BaseSettings


@dataclass
class ApiRoute:
    prefix: str
    tags: List[str] = field(default_factory=list)

    def dict(self) -> Dict:
        return asdict(self)

    def concat(self, other: Union[ApiRoute, str]) -> ApiRoute:
        if isinstance(other, ApiRoute):
            return ApiRoute(
                prefix=self.prefix + other.prefix, tags=self.tags + other.tags
            )
        else:
            return ApiRoute(prefix=self.prefix + "/" + other, tags=self.tags)

    def __str__(self) -> str:
        return self.prefix

    def path(self) -> str:
        return ("/" + self.prefix).replace("//", "/")

    def remove_from(self, id_with_path):
        """Removes API path information from the passed parameter"""
        if isinstance(id_with_path, list):
            return [s.replace(self.prefix, '').replace('/', '')
                    for s in id_with_path]
        else:
            return id_with_path.replace(self.prefix, '').replace('/', '')


class Settings(BaseSettings):
    APPLICATION_NAME: str = "Keepem"
    APPLICATION_TECHNICAL_NAME: str = "Keepem"

    API_V1: ApiRoute = ApiRoute(prefix="/api/v1")
    API_TOKEN: ApiRoute = ApiRoute(prefix="/token", tags=["authentication"])
    API_ASSET_PATH: ApiRoute = ApiRoute(prefix="/assets", tags=["assets"])
    API_USER_PATH: ApiRoute = ApiRoute(prefix="/users", tags=["users"])

    API_RELEASE: ApiRoute = ApiRoute(prefix="/releases", tags=["releases"])
    API_ASSET_BOTTLE: ApiRoute = ApiRoute("/in-a-bottle")
    API_FUTURE_SELF = ApiRoute("/to-future-self")
    API_STASH = ApiRoute("/stash")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 3000  # TODO change me
    UPLOAD_AUTH_TOKEN_EXPIRE_SEC: int = 30
    # to get a string like this run:
    # openssl rand -hex 32
    SECRET_KEY = (
        "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    )
    ALGORITHM = "HS256"
    DATA_FOLDER = path.join(
        path.dirname(path.dirname(path.abspath(__file__))), "data"
    )


settings = Settings()
