import json
import typing
from ast import literal_eval

from core.src.world.components import ComponentType
from core.src.world.components._types_ import ComponentTypeEnum


class AttributesComponent(ComponentType):
    component_enum = ComponentTypeEnum.ATTRIBUTES
    key = ComponentTypeEnum.ATTRIBUTES.value
    component_type = dict
    libname = "attributes"

    @classmethod
    def from_bytes(cls, data: bytes):
        assert data
        return cls(literal_eval(data.decode()))

    def __init__(self, value: dict):
        super().__init__(value)
        self._prev_pos = None
        self._component_values = {
            'name', 'description', 'keyword'
        }

    def __str__(self):
        return str(self.value)

    @property
    def value(self) -> typing.List[dict]:
        return self._value

    @classmethod
    async def get(cls, entity_id: int, repo=None) -> typing.Optional['AttributesComponent']:
        if not repo:
            from core.src.world.builder import world_repository as repo
        return await repo.get_entity_position(entity_id)

    @property
    def serialized(self):
        return json.dumps(self.value)

    @property
    def name(self):
        return self._value.get('name')

    @property
    def description(self):
        return self._value.get('description')

    @property
    def keyword(self):
        return self._value.get('keyword')
