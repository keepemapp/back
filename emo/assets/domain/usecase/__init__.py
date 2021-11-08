from emo.assets.domain.usecase import create_asset as ca
from emo.assets.domain.usecase import asset_to_future_self as nfs
from emo.assets.domain.usecase import time_capsule as tc
from emo.assets.domain.usecase import asset_in_a_bottle as b
from emo.assets.domain.usecase import transfer as tr
from emo.assets.domain.usecase import stash as st
import emo.assets.domain.usecase.asset_handlers as av

import emo.assets.domain.entity.asset_release as ar

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
}
