from abc import ABC, abstractmethod
from typing import Dict

from pymongo import MongoClient
from pymongo.client_session import ClientSession

from kpm.settings import settings as s
from kpm.shared.domain.model import RootAggregate
from kpm.shared.log import logger


class MongoBase(ABC):
    """
    Base class for managing mongo sessions.

    *IMPORTANT:* This class needs to be the FIRST parent

    ```
    class AssetMongoRepo(MongoBase, AssetRepository):
    def __init__(
        self,
        mongo_db: str = "assets",
        mongo_url: str = s.MONGODB_URL,

    ):
        super().__init__(mongo_url=mongo_url)
        self._assets = self._client[mongo_db].assets
        ...
    ```
    """

    def __init__(self, mongo_url: str = s.MONGODB_URL, **kwargs):
        super().__init__(**kwargs)
        print(mongo_url)
        self._client = MongoClient(mongo_url)
        self._tx_session = None

    @staticmethod
    @abstractmethod
    def _to_bson(agg: RootAggregate) -> Dict:
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _from_bson(bson: Dict) -> RootAggregate:
        raise NotImplementedError

    def _insert(self, collection, document):
        self._start_transaction()
        return collection.insert_one(document, session=self._tx_session)

    def _update(self, collection, filter, document):
        self._start_transaction()
        logger.debug(f"Adding to '{collection.name}' document {document}")
        return collection.replace_one(
            filter, document, upsert=True, session=self._tx_session
        )

    def _remove(self, collection, filter):
        self._start_transaction()
        return collection.delete_one(filter, session=self._tx_session)

    def _start_transaction(self):
        if not isinstance(self._tx_session, ClientSession):
            self._tx_session = self._client.start_session()
            self._tx_session.start_transaction()
        if self._tx_session.has_ended:
            self._tx_session = self._client.start_session()
            self._tx_session.start_transaction()

    def rollback(self):
        if isinstance(self._tx_session, ClientSession):
            if self._tx_session.in_transaction:
                self._tx_session.abort_transaction()
            if not self._tx_session.has_ended:
                self._tx_session.end_session()

    def commit(self) -> None:
        logger.debug("Committing to mongo ")
        if isinstance(self._tx_session, ClientSession):
            self._tx_session.commit_transaction()
            self._tx_session.end_session()
