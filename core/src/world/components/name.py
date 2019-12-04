import typing

from core.src.world.components import ComponentType
from core.src.world.components.types import ComponentTypeEnum


class NameComponent(ComponentType):
    component_enum = ComponentTypeEnum.NAME
    key = ComponentTypeEnum.NAME.value
    component_type = str

    def __init__(self, value: str):
        super().__init__(value)

    @property
    def value(self) -> str:
        return self._value

    @classmethod
    async def get(cls, entity_id: int, repo=None) -> typing.Optional['NameComponent']:
        return await super().get(entity_id, repo)
