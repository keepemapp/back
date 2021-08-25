from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Dict, List
from pydantic import BaseSettings


@dataclass
class ApiRoute:
    prefix: str
    tags: List[str] = field(default_factory=list)

    def dict(self) -> Dict:
        return asdict(self)

    def concat(self, other: ApiRoute) -> ApiRoute:
        return ApiRoute(
            prefix=self.prefix + other.prefix,
            tags=self.tags + other.tags
        )

    def __str__(self) -> str:
        return self.prefix


class Settings(BaseSettings):
    APPLICATION_NAME: str = "My Heritage"
    APPLICATION_TECHNICAL_NAME: str = "my_heritage"

    API_V1: ApiRoute = ApiRoute(prefix="/api/v1")
    API_TOKEN: ApiRoute = ApiRoute(prefix="/token", tags=['authentication'])
    API_ASSET_PATH: ApiRoute = ApiRoute(prefix="/assets", tags=['assets'])
    API_TRANSFER_PATH: ApiRoute = ApiRoute(prefix="/transfers", tags=['transfers'])
    API_USER_PATH: ApiRoute = ApiRoute(prefix="/users", tags=['users'])
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM = "HS256"


settings = Settings()
