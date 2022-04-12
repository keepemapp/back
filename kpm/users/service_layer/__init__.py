from kpm.users.domain import commands as cmds
from kpm.users.domain import events as events
from kpm.users.service_layer import keep_handler as kh
from kpm.users.service_layer import user_handler as uh

EVENT_HANDLERS = {
    events.UserRegistered: [uh.send_new_user_email],
    events.UserActivated: [kh.add_referral_keep_when_user_activated,
                           uh.send_activation_email],
    events.UserRemoved: [kh.remove_all_keeps_of_user],
    events.KeepRequested: [],
    events.KeepAccepted: [],
    events.KeepDeclined: [],
}

COMMAND_HANDLERS = {
    # Users
    cmds.RegisterUser: uh.register_user,
    cmds.ActivateUser: uh.activate,
    cmds.UpdateUser: uh.update_user_attributes,
    cmds.UpdateUserPassword: uh.update_password,
    cmds.RemoveUser: uh.remove_user,
    # Keeps
    cmds.RequestKeep: kh.new_keep,
    cmds.AcceptKeep: kh.accept_keep,
    cmds.DeclineKeep: kh.decline_keep,
}
