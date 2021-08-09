from dataclasses import dataclass

from emo.shared.domain.usecase import Event


# TODO investigate more the problem with TypeError: non-default argument 'X' follows default argument
# It has no solution as of python 3.9, only workarounds
# See https://bugs.python.org/issue36077
@dataclass(frozen=True)
class AssetCreated(Event):
    eventType: str = "asset_created"


@dataclass(frozen=True)
class AssetDeleted(Event):
    eventType: str = "asset_deleted"
