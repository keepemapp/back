from abc import ABC
from typing import Set

from kpm.shared.domain.model import RootAggregate


class DomainRepository(ABC):
    """
    Represents the repository.

    It contains a `seen` variable that will allow us to collect all the
    events from every entity acted on.
    """

    def __init__(self, **kwargs):
        pass

    @property
    def seen(self) -> Set[RootAggregate]:
        return self._seen

    def commit(self):
        """Optional method to be used for commit"""
        pass

    def abort(self):
        """Optional method to abort transactions"""
        pass