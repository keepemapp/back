import copy
from typing import Dict, List, Type

from fastapi import BackgroundTasks, Depends

import kpm.assets.adapters.memrepo.views_asset as av_mem
import kpm.assets.adapters.memrepo.views_asset_release as arv_mem
import kpm.assets.adapters.mongo.views_asset as av_mongo
import kpm.assets.adapters.mongo.views_asset_release as arv_mongo
import kpm.users.adapters.memrepo.views as uv_mem
import kpm.users.adapters.mongo.views as uv_mongo
from kpm.assets.domain import Asset, AssetRelease
from kpm.assets.entrypoints.fastapi.dependencies import uows as a_uows
from kpm.assets.service_layer import COMMAND_HANDLERS as a_cmds, \
    EVENT_HANDLERS as a_evs
from kpm.settings import settings as s
from kpm.shared.adapters.mongo import MongoUoW
from kpm.shared.adapters.notifications import (
    EmailNotifications,
    NoNotifications,
)
from kpm.shared.domain.events import Event
from kpm.shared.entrypoints.bootstrap import bootstrap
from kpm.shared.service_layer.message_bus import MessageBus, UoWs
from kpm.users.domain.model import User
from kpm.users.entrypoints.fastapi.dependencies import uows as u_uows
from kpm.users.service_layer import COMMAND_HANDLERS as u_cmds, \
    EVENT_HANDLERS as u_evs

HandlerDict = Dict[Type[Event], List]


def _append_event_handlers(
    handler1: HandlerDict, handler2: HandlerDict
) -> HandlerDict:
    """Merges event handlers by appending values

    TODO we should cache this call. Since it gets executed every request
    lru_cache does not accept dictionaries though
    """
    res = copy.deepcopy(handler1)
    for key, value in handler2.items():
        if key in res:
            res[key].extend(value)
        else:
            res[key] = value
    return res


def message_bus(
    background_tasks: BackgroundTasks,
    asset_uows: UoWs = Depends(a_uows),
    user_uows: UoWs = Depends(u_uows),
) -> MessageBus:
    asset_uows.update(user_uows)
    events = _append_event_handlers(a_evs, u_evs)
    commands = {**a_cmds, **u_cmds}

    email_notifications = NoNotifications()
    if s.EMAIL_SENDER_ADDRESS and s.EMAIL_SENDER_PASSWORD:
        email_notifications = EmailNotifications(background_tasks)

    yield bootstrap(
        uows=asset_uows,
        event_handlers=events,
        command_handlers=commands,
        email_notifications=email_notifications,
    )


def asset_view(bus: MessageBus = Depends(message_bus)):
    if isinstance(bus.uows.get(Asset), MongoUoW):
        return av_mongo
    else:
        return av_mem


def asset_rel_view(bus: MessageBus = Depends(message_bus)):
    if isinstance(bus.uows.get(AssetRelease), MongoUoW):
        return arv_mongo
    else:
        return arv_mem


def user_view(bus: MessageBus = Depends(message_bus)):
    if isinstance(bus.uows.get(User), MongoUoW):
        return uv_mongo
    else:
        return uv_mem
