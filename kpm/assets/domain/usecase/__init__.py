import kpm.assets.domain.entity.asset_release as ar
import kpm.assets.domain.usecase.asset_handlers as av
from kpm.assets.domain.usecase import asset_in_a_bottle as b
from kpm.assets.domain.usecase import asset_to_future_self as nfs
from kpm.assets.domain.usecase import create_asset as ca
from kpm.assets.domain.usecase import release_handlers as rh
from kpm.assets.domain.usecase import stash as st
from kpm.assets.domain.usecase import time_capsule as tc
from kpm.assets.domain.usecase import transfer as tr

EVENT_HANDLERS = {
    ar.AssetReleaseScheduled: [av.hide_asset],
    ar.AssetReleaseCanceled: [av.make_asset_visible],
    ar.AssetReleased: [av.change_asset_owner, av.make_asset_visible],
}

COMMAND_HANDLERS = {
    ca.CreateAsset: ca.create_asset,
    nfs.CreateAssetToFutureSelf: nfs.create_asset_future_self,
    tc.CreateTimeCapsule: tc.create_time_capsule,
    b.CreateAssetInABottle: b.create_asset_in_a_bottle,
    tr.TransferAssets: tr.transfer_asset,
    st.Stash: st.stash_asset,
    rh.CancelRelease: rh.cancel_release,
    rh.TriggerRelease: rh.trigger_release,
}
