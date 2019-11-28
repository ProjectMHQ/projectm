import json
import typing

from core.src.world.components import ComponentType
from core.src.world.components.types import ComponentTypeEnum


class PosComponent(ComponentType):
    component_enum = ComponentTypeEnum.POS
    key = ComponentTypeEnum.POS.value
    component_type = list

    def __init__(self, value: list):
        super().__init__(value)

    def __str__(self):
        return 'x: {}, y:{}, z: {}'.format(self.x, self.y, self.z)

    @property
    def value(self) -> typing.List[int]:
        return self._value

    @classmethod
    def get(cls, entity_id: int, repo=None) -> typing.Optional['PosComponent']:
        if not repo:
            from core.src.world.builder import world_repository as repo
        return repo.get_entity_position(entity_id)

    @property
    def serialized(self):
        return json.dumps(self.value)

    @property
    def x(self):
        return self._value[0]

    @property
    def y(self):
        return self._value[1]

    @property
    def z(self):
        return self._value[2]

    def as_tuple(self):
        return tuple(self.value)
