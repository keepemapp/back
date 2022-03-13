import re
from dataclasses import asdict
from typing import Dict, List, NoReturn, Optional

import pymongo

from kpm.assets.domain import AssetRelease
from kpm.assets.domain.model import (
    Asset,
    DuplicatedAssetException,
    FileData,
    dict_to_release_cond,
)
from kpm.assets.domain.repositories import (
    AssetReleaseRepository,
    AssetRepository,
)
from kpm.settings import settings as s
from kpm.shared.adapters.mongo import MongoBase
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import (
    FINAL_STATES,
    VISIBLE_STATES,
    AssetId,
    RootAggState,
    UserId,
)
from kpm.shared.log import logger


class AssetMongoRepo(MongoBase, AssetRepository):
    def __init__(
        self,
        mongo_db: str = "assets",
        mongo_url: str = s.MONGODB_URL,
    ):
        super().__init__(mongo_url=mongo_url)
        self._assets = self._client[mongo_db].assets

    def _query(
        self,
        *,
        ids: List[AssetId] = None,
        owners: List[UserId] = None,
        order_by: str = None,
        order: str = "asc",
        visible_only: bool = True,
        asset_types: List[str] = None,
        bookmarked: Optional[bool] = None,
    ) -> List[Asset]:

        find_dict = {}

        if ids:
            find_dict["_id"] = {"$in": [aid.id for aid in ids]}
        if owners:
            find_dict["owners_id"] = {"$in": [o.id for o in owners]}
        if visible_only:
            find_dict["state"] = {"$in": [st.value for st in VISIBLE_STATES]}
        else:
            find_dict["state"] = {
                "$not": re.compile(RootAggState.REMOVED.value)
            }
        if asset_types:
            find_dict["file.type"] = {"$in": asset_types}
        if isinstance(bookmarked, bool):
            find_dict["bookmarked"] = bookmarked

        logger.info(f"Mongo query filters {find_dict}")
        resps = self._assets.find(find_dict)
        if order_by:
            orval = (
                pymongo.DESCENDING if order == "desc" else pymongo.ASCENDING
            )
            resps = resps.sort(order_by, orval)
        res = []
        for a in resps:
            res.append(self._from_bson(a))
        logger.info(f"Mongo response count: {len(res)}")
        return res

    @staticmethod
    def _to_bson(agg: Asset) -> Dict:
        bson = asdict(agg)
        bson["_id"] = bson.pop("id")["id"]
        bson["owners_id"] = [o["id"] for o in bson.pop("owners_id")]
        bson.pop("events")
        bson["state"] = bson.pop("state").value
        bson["tags"] = list(bson.pop("tags"))
        bson["people"] = list(bson.pop("people"))
        return bson

    @staticmethod
    def _from_bson(bson: Dict) -> Asset:
        bson["id"] = AssetId(id=bson.pop("_id"))
        bson["owners_id"] = [UserId(id=o) for o in bson.pop("owners_id")]
        bson["file"] = FileData(**bson.pop("file"))
        return Asset(loaded_from_db=True, **bson)

    def create(self, asset: Asset) -> NoReturn:
        logger.info(f"Creating asset with id '{asset.id.id}'")
        if self._assets.find_one({"_id": asset.id.id}):
            raise DuplicatedAssetException()
        self._insert(self._assets, self._to_bson(asset))
        self._seen.add(asset)

    def update(self, asset: Asset) -> None:
        bson = self._to_bson(asset)
        logger.info(f"Updating asset with id '{asset.id.id}'")
        self._update(self._assets, {"_id": bson["_id"]}, bson)
        self._seen.add(asset)

    def remove(self, id: AssetId) -> NoReturn:
        res = self._remove(self._assets, {"_id": id.id})
        logger.info(
            f"Mongo deletion of id: '{id.id}' "
            f"with count {res.deleted_count}"
        )


class AssetReleaseMongoRepo(MongoBase, AssetReleaseRepository):
    def __init__(
        self,
        mongo_db: str = "assets",
        mongo_url: str = s.MONGODB_URL,
    ):
        super().__init__(mongo_url=mongo_url)
        self._legacy = self._client[mongo_db].legacy

    def _to_bson(self, agg: AssetRelease) -> Dict:
        bson = asdict(agg)
        bson["_id"] = bson.pop("id")["id"]
        bson["owner"] = bson.pop("owner")["id"]
        bson["receivers"] = [r["id"] for r in bson.pop("receivers")]
        bson["assets"] = [r["id"] for r in bson.pop("assets")]
        bson.pop("events")
        bson["state"] = bson.pop("state").value
        bson["bequest_type"] = bson.pop("bequest_type").value
        return bson

    def _from_bson(self, bson: Dict) -> AssetRelease:
        bson["id"] = DomainId(id=bson.pop("_id"))
        bson["owner"] = UserId(id=bson.pop("owner"))
        bson["receivers"] = [UserId(id=o) for o in bson.pop("receivers")]
        bson["assets"] = [AssetId(id=o) for o in bson.pop("assets")]
        bson["conditions"] = [
            dict_to_release_cond(c) for c in bson.pop("conditions")
        ]
        return AssetRelease(loaded_from_db=True, **bson)

    def put(self, release: AssetRelease):
        bson = self._to_bson(release)
        self._update(self._legacy, {"_id": bson["_id"]}, bson)
        self._seen.add(release)

    def exists(self, owner: UserId, name: str) -> bool:
        find_dict = {"owner": owner.id, "name": name}
        return self._legacy.count_documents(find_dict) > 0

    def get(self, release_id: DomainId) -> Optional[AssetRelease]:
        find_dict = {"_id": release_id.id}
        resp = self._legacy.find_one(find_dict)
        if resp:
            return self._from_bson(resp)

    def user_active_releases(self, user_id: UserId) -> List[AssetRelease]:
        return self.all(owner=user_id.id, pending=True)

    def user_past_releases(self, user_id: UserId) -> List[AssetRelease]:
        return self.all(owner=user_id.id, pending=False)

    def all(
        self,
        owner: str = None,
        receiver: str = None,
        extra_conditions: Dict = None,
        pending: bool = None,
    ) -> List[AssetRelease]:
        find_dict = {}
        if owner:
            find_dict["owner"] = owner
        if receiver:
            find_dict["receiver"] = receiver
        if extra_conditions:
            find_dict.update(extra_conditions)
        if pending is not None:
            if pending:
                find_dict["state"] = RootAggState.ACTIVE.value
            else:
                find_dict["state"] = {
                    "$in": [st.value for st in FINAL_STATES]
                }

        logger.info(f"Mongo query filters {find_dict}")
        resps = self._legacy.find(find_dict)
        res = []
        for a in resps:
            res.append(self._from_bson(a))
        logger.info(f"Mongo response count: {len(res)}")
        return res
