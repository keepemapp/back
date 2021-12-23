from __future__ import annotations

from kpm.assets.domain.repositories import AssetRepository
from kpm.shared.service_layer.unit_of_work import AbstractUnitOfWork


class AssetUoW(AbstractUnitOfWork):
    repo: AssetRepository

    def __enter__(self):
        return super().__enter__()
