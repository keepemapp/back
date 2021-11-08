from emo.assets.domain.usecase.unit_of_work import AssetUoW
from emo.assets.infra.memrepo.repository import MemoryPersistedAssetRepository


class AssetMemoryUnitOfWork(AssetUoW):
    def __init__(self) -> None:
        super().__init__()
        self.committed = False

    def __enter__(self):
        self.repo = MemoryPersistedAssetRepository()
        return super().__enter__()

    def _commit(self):
        self.repo.__persist()
        self.committed = True

    def rollback(self):
        pass
