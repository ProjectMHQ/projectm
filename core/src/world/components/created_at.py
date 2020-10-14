import typing

from core.src.world.components import ComponentType
from core.src.world.components._types_ import ComponentTypeEnum


class CreatedAtComponent(ComponentType):
    component_enum = ComponentTypeEnum.CREATED_AT
    key = ComponentTypeEnum.CREATED_AT.value
    component_type = int
    libname = "created_at"

    def __init__(self, value: int):
        super().__init__(value)

    @property
    def value(self) -> int:
        return self._value

    @classmethod
    async def get(cls, entity_id: int, repo=None) -> typing.Optional['CreatedAtComponent']:
        return await super().get(entity_id, repo)
