import os
from pathlib import Path
from tempfile import TemporaryFile
from typing import Union

import aiofiles

from kpm.settings import settings


class AssetFileRepository:
    def __init__(
        self,
        base_path: Union[Path, str] = Path(
            os.path.join(settings.DATA_FOLDER, "assets")
        ),
    ):
        self._base_path = base_path

    @staticmethod
    def location_to_list(location: str):
        return location.split("/") if "/" in location else location.split("\\")

    async def create(self, location: str, file: TemporaryFile):
        loc_split = self.location_to_list(location)
        base_path = Path(self._base_path, loc_split[0])
        base_path.mkdir(exist_ok=True)
        file_path = os.path.join(base_path, loc_split[1])
        async with aiofiles.open(file_path, "wb") as of:
            while content := await file.read(1024):
                await of.write(content)

    def delete(self, location: str):
        loc_split = self.location_to_list(location)
        file_path = os.path.join(self._base_path, *loc_split)
        if os.path.exists(file_path):
            os.remove(file_path)

    def get(self, location: str):
        loc_split = self.location_to_list(location)
        file_path = os.path.join(self._base_path, *loc_split)
        # FIXME this is wrong. We should not depend on FASTAPI magic
        return file_path
