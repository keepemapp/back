from kpm.users.domain import commands as cmds
from kpm.users.domain import events as events
from kpm.users.service_layer import user_handler as uh

EVENT_HANDLERS = {
    events.UserRegistered: [uh.send_welcome_email],
}

COMMAND_HANDLERS = {
    cmds.RegisterUser: uh.register_user,
}
