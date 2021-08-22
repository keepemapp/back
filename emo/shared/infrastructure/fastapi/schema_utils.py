from typing import Type, TypeVar
from dataclasses import asdict
from pydantic import BaseModel

from emo.shared.domain import Entity

T = TypeVar("T", bound=BaseModel)


def to_pydantic_model(entity: Entity, model: Type[T]) -> T:
    keys = list(model.__fields__.keys())
    e = asdict(entity)
    e['id'] = e['id']['id']
    res = {k: e.get(k) for k in keys}
    return model(**res)
