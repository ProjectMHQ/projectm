import typing

from core.src.world.components import ComponentType
from core.src.world.components._types_ import ComponentTypeEnum


class CharacterComponent(ComponentType):
    component_enum = ComponentTypeEnum.CHARACTER
    key = ComponentTypeEnum.CHARACTER.value
    component_type = bool
    libname = "character"

    def __init__(self, value: (int, bool)):
        if not isinstance(value, bool):
            assert value in (0, 1), value
            value = bool(int)
        super().__init__(value)

    @property
    def value(self) -> bool:
        return self._value

    @classmethod
    async def get(cls, entity_id: bool, repo=None) -> typing.Optional['CharacterComponent']:
        return await super().get(entity_id, repo)

    def as_int(self):
        return int(self._value)