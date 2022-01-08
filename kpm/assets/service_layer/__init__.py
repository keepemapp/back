import kpm.assets.domain.events as events
from kpm.assets.domain import commands as cmds
from kpm.assets.service_layer import asset_handlers as ah
from kpm.assets.service_layer import transfer_handlers as th

EVENT_HANDLERS = {
    events.AssetReleaseScheduled: [ah.hide_asset],
    events.AssetReleaseCanceled: [ah.make_asset_visible],
    events.AssetReleased: [ah.change_asset_owner, ah.make_asset_visible],
    events.AssetOwnershipChanged: [],
}
COMMAND_HANDLERS = {
    cmds.CreateAsset: ah.create_asset,
    cmds.UpdateAssetFields: ah.update_asset_fields,
    cmds.UploadAssetFile: ah.asset_file_upload,
    cmds.CreateAssetToFutureSelf: th.create_asset_future_self,
    cmds.CreateTimeCapsule: th.create_time_capsule,
    cmds.CreateAssetInABottle: th.create_asset_in_a_bottle,
    cmds.TransferAssets: th.transfer_asset,
    cmds.Stash: th.stash_asset,
    cmds.CancelRelease: th.cancel_release,
    cmds.TriggerRelease: th.trigger_release,
}
