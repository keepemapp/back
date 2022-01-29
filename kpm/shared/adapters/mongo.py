from abc import ABC, abstractmethod
from typing import Dict, Type

from pymongo import MongoClient
from pymongo.client_session import ClientSession

from kpm.settings import settings as s
from kpm.shared.domain.model import RootAggregate
from kpm.shared.domain.repository import DomainRepository
from kpm.shared.log import logger
from kpm.shared.service_layer.unit_of_work import AbstractUnitOfWork

R = Type[DomainRepository]


class MongoUoW(AbstractUnitOfWork):
    def __init__(self, repo_cls: R, **kwargs) -> None:
        super().__init__()
        self.__repo_cls = repo_cls
        self.__repo_kwargs = kwargs
        self.committed = False
        self.repo = None

    def __enter__(self):
        self.committed = False

        self.repo: DomainRepository = self.__repo_cls(**self.__repo_kwargs)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if isinstance(self.repo, MongoBase):
            self.repo.close_conn()

    def _commit(self):
        if len(self.repo.seen) > 0:
            self.repo.commit()
        self.committed = True

    def rollback(self):
        self.repo.rollback()


def mongo_client(mongo_url: str = s.MONGODB_URL) -> MongoClient:
    if s.MONGODB_USER and s.MONGODB_PWD:
        return MongoClient(
            mongo_url,
            user=s.MONGODB_USER,
            password=s.MONGODB_PWD
        )
    else:
        return MongoClient(mongo_url)


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
        self._client = mongo_client(mongo_url)
        self._tx_session = None

    def close_conn(self):
        self._client.close()

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
        logger.debug(f"Adding to '{collection.name}' document {document}")
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
        self.close_conn()

    def commit(self) -> None:
        logger.debug("Committing to mongo ")
        if isinstance(self._tx_session, ClientSession):
            self._tx_session.commit_transaction()
            self._tx_session.end_session()
        self.close_conn()