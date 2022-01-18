import os
import pickle
import re
from dataclasses import asdict
from pathlib import Path
import pprint
import json
from typing import Dict, List, NoReturn, Optional, Set, Union

import pymongo
from pydantic.json import pydantic_encoder
from bson import ObjectId
from pymongo import MongoClient
from pymongo.client_session import ClientSession

from kpm.assets.domain.model import (
    Asset,
    AssetRelease,
    DuplicatedAssetException, FileData,
)
from kpm.assets.domain.repositories import (
    AssetReleaseRepository,
    AssetRepository,
)
from kpm.settings import settings as s
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import AssetId, RootAggState, UserId, \
    VISIBLE_STATES
from kpm.shared.log import logger

Assets = Dict[AssetId, Asset]
OwnerIndex = Dict[UserId, Set[AssetId]]


class AssetMongoRepo(AssetRepository):
    def __init__(
        self,
        mongo_url: str = s.MONGODB_URL,
        mongo_db: str = "assets",

    ):
        super(AssetMongoRepo, self).__init__()
        self._client = MongoClient(mongo_url)
        self._assets = self._client[mongo_db].assets
        self._tx_session = None

    def _query(
        self,
        *,
        ids: List[AssetId] = None,
        owners: List[UserId] = None,
        order_by: str = None,
        order: str = "asc",
        visible_only: bool = True,
        asset_types: List[str] = None,
        bookmarked: Optional[bool] = None
    ) -> List[Asset]:

        find_dict = {}

        if ids:
            find_dict['_id'] = {'$in': [aid.id for aid in ids]}
        if owners:
            find_dict['owners_id'] = {
                '$elemMatch': {'id': {'$in': [o.id for o in owners]}}
            }
        if visible_only:
            find_dict['state'] = {'$in': [st.value for st in VISIBLE_STATES]}
        else:
            find_dict['state'] = {
                '$not': re.compile(RootAggState.REMOVED.value)}
        if asset_types:
            find_dict['file.type'] = {'$in': asset_types}
        if isinstance(bookmarked, bool):
            find_dict['bookmarked'] = bookmarked

        logger.info(f"Mongo query filters {find_dict}")
        resps = self._assets.find(find_dict)
        if order_by:
            orval = pymongo.DESCENDING if order == 'desc' else pymongo.ASCENDING
            resps = resps.sort(order_by, orval)
        res = []
        for a in resps:
            a['id'] = AssetId(a.pop('_id'))
            a['owners_id'] = [UserId(o['id']) for o in a.pop('owners_id')]
            a['file'] = FileData(**a.pop('file'))
            res.append(Asset(**a))
        logger.info(f"Mongo response count: {len(res)}")
        return res

    def _to_bson(self, asset: Asset) -> Dict:
        bson = asdict(asset)
        bson['_id'] = bson.pop('id')['id']
        bson.pop("events")
        bson['state'] = bson.pop("state").value
        bson['tags'] = list(bson.pop("tags"))
        bson['people'] = list(bson.pop("people"))
        return bson

    def create(self, asset: Asset) -> NoReturn:
        logger.info(f"Creating asset with id '{asset.id.id}'")
        if self._assets.find_one({"_id": asset.id.id}):
            raise DuplicatedAssetException()
        self._start_transaction()
        self._assets.insert_one(self._to_bson(asset), session=self._tx_session)
        self._seen.add(asset)

    def update(self, asset: Asset) -> None:
        self._start_transaction()
        bson = self._to_bson(asset)
        logger.info(f"Updating asset with id '{asset.id.id}'")
        self._assets.replace_one(
            {'_id': bson['_id']}, bson, session=self._tx_session
        )
        self._seen.add(asset)

    def remove(self, id: AssetId) -> NoReturn:
        self._start_transaction()
        res = self._assets.delete_one({'_id': id.id}, session=self._tx_session)
        logger.info(f"Mongo deletion of id: '{id.id}' "
                    f"with count {res.deleted_count}")

    def _start_transaction(self):
        if not isinstance(self._tx_session, ClientSession):
            self._tx_session = self._client.start_session()
            self._tx_session.start_transaction()
        if self._tx_session.has_ended:
            self._tx_session = self._client.start_session()
            self._tx_session.start_transaction()

    def rollback(self):
        if isinstance(self._tx_session, ClientSession):
            self._tx_session.abort_transaction()
            self._tx_session.end_session()

    def commit(self) -> None:
        if isinstance(self._tx_session, ClientSession):
            self._tx_session.commit_transaction()
            self._tx_session.end_session()

