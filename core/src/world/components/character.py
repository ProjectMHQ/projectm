import typing

from core.src.world.components import ComponentType
from core.src.world.components._types_ import ComponentTypeEnum


class CharacterComponent(ComponentType):
    component_enum = ComponentTypeEnum.CHARACTER
    key = ComponentTypeEnum.CHARACTER.value
    component_type = bool

    def __init__(self, value: bool):
        super().__init__(value)

    @property
    def value(self) -> bool:
        return self._value

    @classmethod
    async def get(cls, entity_id: bool, repo=None) -> typing.Optional['CharacterComponent']:
        return await super().get(entity_id, repo)
