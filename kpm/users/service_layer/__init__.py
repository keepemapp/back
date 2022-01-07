from kpm.users.domain import commands as cmds
from kpm.users.domain import events as events
from kpm.users.service_layer import keep_handler as kh
from kpm.users.service_layer import user_handler as uh

EVENT_HANDLERS = {
    events.UserRegistered: [uh.send_welcome_email],
    events.UserActivated: [],
    events.KeepRequested: [],
    events.KeepAccepted: [],
    events.KeepDeclined: [],
}

COMMAND_HANDLERS = {
    cmds.RegisterUser: uh.register_user,
    cmds.RequestKeep: kh.new_keep,
    cmds.AcceptKeep: kh.accept_keep,
    cmds.DeclineKeep: kh.decline_keep,
}
