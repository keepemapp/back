from emo.assets.domain.usecase import create_asset as ca
from emo.assets.domain.usecase import note_to_future_self as nfs
from emo.assets.domain.usecase import time_capsule as tc

EVENT_HANDLERS = {}

COMMAND_HANDLERS = {
    ca.CreateAsset: ca.create_asset,
    nfs.CreateNoteToFutureSelf: nfs.create_note_future_self,
    tc.CreateTimeCapsule: tc.create_time_capsule,
}
