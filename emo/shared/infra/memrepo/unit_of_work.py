from typing import TypeVar, Type
from emo.shared.domain.usecase.unit_of_work import AbstractUnitOfWork
from emo.assets.infra.memrepo.repository import MemoryPersistedAssetRepository
from emo.shared.domain import DomainRepository


R = Type[DomainRepository]


class MemoryUoW(AbstractUnitOfWork):
    def __init__(self, repo_cls: R, **kwargs) -> None:
        super().__init__()
        self.__repo_cls = repo_cls
        self.__repo_kwargs = kwargs
        self.committed = False

    def __enter__(self):
        self.committed = False
        self.repo: R = R(**self.__repo_kwargs)
        return super().__enter__()

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass
