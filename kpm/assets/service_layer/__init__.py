import kpm.assets.domain.events as events
from kpm.assets.domain import commands as cmds
from kpm.assets.service_layer import asset_handlers as ah
from kpm.assets.service_layer import transfer_handlers as th
from kpm.users.domain.events import UserRemoved

EVENT_HANDLERS = {
    events.AssetReleaseScheduled: [ah.hide_asset],
    events.AssetReleaseCanceled: [
        ah.make_asset_visible,
        # th.notify_transfer_cancellation,
    ],
    events.AssetReleased: [ah.change_asset_owner, ah.make_asset_visible],
    events.AssetOwnershipChanged: [],
    UserRemoved: [th.remove_user_releases, ah.remove_user_assets],
}
COMMAND_HANDLERS = {
    cmds.CreateAsset: ah.create_asset,
    cmds.UpdateAssetFields: ah.update_asset_fields,
    cmds.RemoveAsset: ah.remove_asset,
    cmds.UploadAssetFile: ah.asset_file_upload,
    cmds.CreateAssetToFutureSelf: th.create_asset_future_self,
    cmds.CreateTimeCapsule: th.create_time_capsule,
    cmds.CreateAssetInABottle: th.create_asset_in_a_bottle,
    cmds.CreateTransfer: th.transfer_asset,
    cmds.CreateHideAndSeek: th.hide_asset,
    cmds.CancelRelease: th.cancel_release,
    cmds.TriggerRelease: th.trigger_release,
}
