from __future__ import annotations

from emo.assets.domain.entity import AssetRepository
from emo.shared.domain.usecase.unit_of_work import AbstractUnitOfWork


class AssetUoW(AbstractUnitOfWork):
    repo: AssetRepository

    def __enter__(self):
        return super().__enter__()
