import random

import pytest

from kpm.shared.adapters.mongo import MongoUoW
from kpm.shared.entrypoints import bootstrap
from kpm.shared.service_layer.message_bus import UoWs
from kpm.users.adapters.mongo.repository import (
    KeepMongoRepo,
    SessionMongoRepo,
    UserMongoRepo,
)
from kpm.users.domain.model import Keep, Session, User
from kpm.users.service_layer import COMMAND_HANDLERS, EVENT_HANDLERS
from tests.shared.utils import TestUoW
from tests.users.adapters.mongo.test_repository import mongo_client
from tests.users.utils import MemoryUserRepository, TestKeepRepository


@pytest.fixture
def bus(mongo_client):
    """Init test bus for passing it to tests"""
    db = "users_" + "".join(random.choice("smiwysndkajsown") for _ in range(5))
    yield bootstrap.bootstrap(
        uows=UoWs(
            {
                User: MongoUoW(UserMongoRepo, mongo_db=db),
                Keep: MongoUoW(KeepMongoRepo, mongo_db=db),
                Session: MongoUoW(SessionMongoRepo, mongo_db=db),
            }
        ),
        event_handlers=EVENT_HANDLERS,
        command_handlers=COMMAND_HANDLERS,
    )
    with mongo_client as client:
        client.drop_database(db)
