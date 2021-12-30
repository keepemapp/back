from fastapi import Depends

from kpm.assets.entrypoints.fastapi.dependencies import uows as a_uows
from kpm.users.entrypoints.fastapi.dependencies import uows as u_uows
from kpm.shared.entrypoints.bootstrap import bootstrap
from kpm.shared.service_layer.message_bus import MessageBus, UoWs


def message_bus(asset_uows: UoWs = Depends(a_uows),
                user_uows: UoWs = Depends(u_uows),
                ) -> MessageBus:
    asset_uows.update(user_uows)
    yield bootstrap(uows=asset_uows)