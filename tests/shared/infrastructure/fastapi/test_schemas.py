import pytest
from pydantic import BaseModel, ValidationError

from emo.shared.domain import DomainId
from emo.shared.domain.usecase import Entity
from emo.shared.infrastructure.fastapi.schema_utils import to_pydantic_model


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
            p = to_pydantic_model(e, EntityPyd)
