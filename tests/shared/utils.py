from typing import Type

from kpm.shared.domain.repository import DomainRepository
from kpm.shared.service_layer.unit_of_work import AbstractUnitOfWork


class TestUoW(AbstractUnitOfWork):
    def __init__(self, repo_cls: Type[DomainRepository], **kwargs) -> None:
        super().__init__()
        self.committed = False
        self.repo = repo_cls(**kwargs)

    def __enter__(self):
        self.committed = False
        return super().__enter__()

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass
