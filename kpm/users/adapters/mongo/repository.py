from dataclasses import asdict
from typing import Dict, List, Optional

from pymongo.collation import Collation

from kpm.settings import settings as s
from kpm.shared.adapters.mongo import MongoBase
from kpm.shared.domain import DomainId
from kpm.shared.domain.model import RootAggregate, UserId
from kpm.shared.log import logger
from kpm.users.domain.model import Keep, User
from kpm.users.domain.repositories import KeepRepository, UserRepository


class UserMongoRepo(MongoBase, UserRepository):
    def __init__(
        self,
        mongo_db: str = "users",
        mongo_url: str = s.MONGODB_URL,
    ):
        super().__init__(mongo_url=mongo_url)
        self._coll = self._client[mongo_db].users

    def all(self) -> List[User]:
        find_dict = {}
        logger.info(f"Mongo query filters {find_dict}")
        resps = self._coll.find(find_dict)
        res = []
        for a in resps:
            res.append(self._from_bson(a))
        logger.info(f"Mongo response count: {len(res)}")
        return res

    def get(self, uid: UserId) -> Optional[User]:
        find_dict = {"_id": uid.id}
        resp = self._coll.find_one(find_dict)
        if resp:
            return self._from_bson(resp)

    def exists_email(self, email: str) -> bool:
        find_dict = {}
        if "@gmail" in email:

            def ignore_dots(email: str) -> str:
                start, end = email.split("@")
                return start.replace(".", "") + "@" + end

            find_dict["email"] = ignore_dots(email)
            collat = Collation(locale="en_US", alternate="shifted")
            logger.debug(f"Searching {find_dict}")
            res = self._coll.find(find_dict, projection=["email"]).collation(
                collat
            )
            for r in res:
                if ignore_dots(email) == ignore_dots(r["email"]):
                    return True

            return False

        else:
            find_dict["email"] = email
            return self._coll.count_documents(find_dict) != 0

    def exists_username(self, username: str) -> bool:
        return self._coll.count_documents({"username": username}) != 0

    def create(self, user: User):
        logger.info(f"Creating user with id '{user.id.id}'")
        self._insert(self._coll, self._to_bson(user))
        self._seen.add(user)

    def update(self, user: User):
        bson = self._to_bson(user)
        logger.info(f"Updating user with id '{user.id.id}'")
        self._update(self._coll, {"_id": bson["_id"]}, bson)
        self._seen.add(user)

    def empty(self) -> bool:
        return self._coll.count_documents({}, limit=2) == 0

    @staticmethod
    def _to_bson(agg: User) -> Dict:
        bson = asdict(agg)
        bson.pop("events")
        bson["_id"] = bson.pop("id")["id"]
        bson["state"] = bson.pop("state").value
        return bson

    @staticmethod
    def _from_bson(bson: Dict) -> User:
        bson["id"] = UserId(id=bson.pop("_id"))
        return User(loaded_from_db=True, **bson)


class KeepMongoRepo(MongoBase, KeepRepository):
    def __init__(
        self,
        mongo_db: str = "users",
        mongo_url: str = s.MONGODB_URL,
    ):
        super().__init__(mongo_url=mongo_url)
        self._coll = self._client[mongo_db].keeps

    def put(self, agg: Keep):
        bson = self._to_bson(agg)
        self._update(self._coll, {"_id": bson["_id"]}, bson)
        self._seen.add(agg)

    def all(self, user: UserId = None) -> List[Keep]:
        find_dict = {}
        logger.info(f"Mongo query filters {find_dict}")
        resps = self._coll.find(find_dict)
        res = []
        for a in resps:
            res.append(self._from_bson(a))
        logger.info(f"Mongo response count: {len(res)}")
        return res

    def get(self, kid: DomainId) -> Keep:
        find_dict = {"_id": kid.id}
        resp = self._coll.find_one(find_dict)
        if resp:
            return self._from_bson(resp)

    def exists(self, user1: UserId, user2: UserId) -> bool:

        cond1 = (
            self._coll.count_documents(
                {"requester": user1.id, "requested": user2.id}
            )
            != 0
        )
        cond2 = (
            self._coll.count_documents(
                {"requester": user2.id, "requested": user1.id}
            )
            != 0
        )
        return cond1 or cond2

    @staticmethod
    def _to_bson(agg: RootAggregate) -> Dict:
        bson = asdict(agg)
        bson.pop("events")
        bson["_id"] = bson.pop("id")["id"]
        bson["state"] = bson.pop("state").value
        bson["requester"] = bson.pop("requester")["id"]
        bson["requested"] = bson.pop("requested")["id"]
        return bson

    @staticmethod
    def _from_bson(bson: Dict) -> Keep:
        bson["id"] = DomainId(id=bson.pop("_id"))
        bson["requester"] = UserId(id=bson.pop("requester"))
        bson["requested"] = UserId(id=bson.pop("requested"))
        return Keep(loaded_from_db=True, **bson)