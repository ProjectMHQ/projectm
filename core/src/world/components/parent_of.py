import json
import typing
from ast import literal_eval

from core.src.world.components import ComponentType
from core.src.world.components._types_ import ComponentTypeEnum


class ParentOfComponent(ComponentType):
    component_enum = ComponentTypeEnum.PARENT_OF
    key = ComponentTypeEnum.PARENT_OF.value
    component_type = list
    libname = "parent_of"

    @classmethod
    def from_bytes(cls, data: bytes):
        assert data
        return cls(literal_eval(data.decode()))

    def __init__(self, entity=None, location: typing.Optional[ComponentType] = None):
        from core.src.world.domain.entity import Entity
        assert isinstance(entity, Entity)
        assert bool(entity) == bool(location)
        if entity and location:
            value = [entity.entity_id, location.component_enum]
        else:
            value = None
        super().__init__(value)

    def __str__(self):
        return str(self.value)

    @property
    def value(self) -> typing.List[list]:
        return self._value

    @classmethod
    async def get(cls, entity_id: int, repo=None) -> typing.Optional['ParentOfComponent']:
        if not repo:
            from core.src.world.builder import world_repository as repo
        return await repo.get_entity_position(entity_id)

    @property
    def serialized(self):
        return json.dumps(self.value)

    @property
    def parent_id(self):
        return self._value[0]

    @property
    def location(self):
        return self._value[1]
