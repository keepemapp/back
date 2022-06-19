from __future__ import annotations

from dataclasses import Field, field
from typing import Callable, TypeVar
from uuid import uuid4

from pydantic.dataclasses import dataclass


def required_field(**kwargs) -> Field:
    def raise_err():
        raise TypeError()

    return field(default_factory=lambda: raise_err, **kwargs)


def required_updatable_field(**kwargs) -> Field:
    def raise_err():
        raise TypeError()

    return updatable_field(default_factory=lambda: raise_err, **kwargs)


def updatable_field(**kwargs) -> Field:
    if "metadata" in kwargs:
        kwargs["metadata"].update({"user_updatable": True})
    else:
        kwargs["metadata"] = {"user_updatable": True}
    if "default" not in kwargs and "default_factory" not in kwargs:
        kwargs["default"] = None
    return field(**kwargs)


@dataclass(frozen=True)
class DomainId:
    id: str

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    # def __str__(self):
    #     return id


def init_id(id_type: Callable = DomainId) -> DomainId:
    return id_type(id=str(uuid4()))


class IdTypeException(Exception):
    """Raise when ID type is not valid"""

    def __init__(self):
        super().__init__("ID Type is not valid")


IDT = TypeVar("IDT", str, DomainId)
