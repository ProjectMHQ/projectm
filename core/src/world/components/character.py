import typing

from core.src.world.components import ComponentType
from core.src.world.components.types import ComponentTypeEnum


class CharacterComponent(ComponentType):
    key = ComponentTypeEnum.CHARACTER.value
    component_type = bool

    def __init__(self, value: bool):
        super().__init__(value)

    @property
    def value(self) -> bool:
        return self._value

    @classmethod
    def get(cls, entity_id: bool, repo=None) -> typing.Optional['CharacterComponent']:
        return super().get(entity_id, repo)
