from typing import Any, List, Type, TypeVar

from pydantic import BaseModel

from kpm.shared.domain import DomainId, Entity

T = TypeVar("T", bound=BaseModel)


def to_base_type(value: Any):
    # Option to improve: pass also the desired type
    if isinstance(value, DomainId):
        return value.id
    if isinstance(value, str):
        return value
    elif isinstance(value, List):
        return [to_base_type(v) for v in value]
    elif isinstance(value, Entity):
        raise Exception("to_base_type does not support extracting entities")
    else:
        return value


def to_pydantic_model(entity: Entity, model: Type[T]) -> T:
    # TODO possibility to use inspect.signature(model).parameters
    keys = [k for k in model.__fields__.keys() if k != "links"]
    res = {k: to_base_type(getattr(entity, k, None)) for k in keys}
    return model(**res)
