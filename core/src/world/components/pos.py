import typing

from core.src.world.components import ComponentType
from core.src.world.components.types import ComponentTypeEnum


class PosComponent(ComponentType):
    component_enum = ComponentTypeEnum.POS
    key = ComponentTypeEnum.POS.value
    component_type = list

    def __init__(self, value: list):
        super().__init__(value)

    @property
    def value(self) -> typing.List[int]:
        return self._value

    @classmethod
    def get(cls, entity_id: int, repo=None) -> typing.Optional['PosComponent']:
        if not repo:
            from core.src.world.builder import world_map_repository as repo
        return repo.get_entity_position(entity_id)
