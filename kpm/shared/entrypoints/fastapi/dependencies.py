from fastapi import Depends

from kpm.assets.entrypoints.fastapi.dependencies import uows as a_uows
from kpm.assets.service_layer import COMMAND_HANDLERS as a_cmds
from kpm.assets.service_layer import EVENT_HANDLERS as a_evs
from kpm.shared.entrypoints.bootstrap import bootstrap
from kpm.shared.service_layer.message_bus import MessageBus, UoWs
from kpm.users.entrypoints.fastapi.dependencies import uows as u_uows
from kpm.users.service_layer import COMMAND_HANDLERS as u_cmds
from kpm.users.service_layer import EVENT_HANDLERS as u_evs


def message_bus(
    asset_uows: UoWs = Depends(a_uows),
    user_uows: UoWs = Depends(u_uows),
) -> MessageBus:
    asset_uows.update(user_uows)
    events = {**a_evs, **u_evs}
    commands = {**a_cmds, **u_cmds}
    yield bootstrap(
        uows=asset_uows, event_handlers=events, command_handlers=commands
    )
