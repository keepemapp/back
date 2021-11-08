from dataclasses import dataclass, field
from typing import List

import pytest
from pydantic import BaseModel, ValidationError
from pydantic.dataclasses import dataclass as pydataclass

from emo.shared.domain import DomainId, Entity, ValueObject
from emo.shared.infra.fastapi.schema_utils import to_pydantic_model


@pytest.mark.unit
class TestPydanticConverter:
    def test_simple_entity(self):
        e = Entity(DomainId("0"))

        class EntityPyd(BaseModel):
            id: str

        p = to_pydantic_model(e, EntityPyd)
        assert p.id == e.id.id

    def test_should_fail_if_model_has_more_keys(self):
        e = Entity(DomainId("0"))

        class EntityPyd(BaseModel):
            id: str
            other_key: str

        with pytest.raises(ValidationError) as _:
            to_pydantic_model(e, EntityPyd)

    def test_list_of_domain_ids(self):
        @dataclass
        class DomainEntity(Entity):
            ids: List[DomainId] = field(default_factory=list)

        class EntityPyd(BaseModel):
            id: str
            ids: List[str]

        e = DomainEntity(
            id=DomainId("id"),
            ids=[DomainId("0"), DomainId("1"), DomainId("2")],
        )

        p = to_pydantic_model(e, EntityPyd)
        assert p.ids == ["0", "1", "2"]
