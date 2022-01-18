from typing import Union, Protocol
from os.path import join, exists
from os import mkdir
from pathlib import Path

from kpm.settings import settings as s


class MongoBase:
    def __init__(
            self,
            db_name: str,
            data_folder: Union[Path, str] = s.DATA_FOLDER,
    ):
        self.db_folder = join(data_folder, db_name)
        if not exists(self.db_folder):
            mkdir(self.db_folder, mode=700)

        self._data: Data = {}

    def _store_data(self):
        pass
