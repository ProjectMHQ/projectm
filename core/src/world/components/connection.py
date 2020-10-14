import typing

from core.src.world.components import ComponentType
from core.src.world.components._types_ import ComponentTypeEnum


class ConnectionComponent(ComponentType):
    component_enum = ComponentTypeEnum.CONNECTION
    key = ComponentTypeEnum.CONNECTION.value
    component_type = str
    libname = "connection"

    def __init__(self, value: str):
        super().__init__(value)

    @property
    def value(self) -> typing.Optional[str]:
        return self._value

    @classmethod
    async def get(cls, entity_id: int, repo=None) -> typing.Optional['ConnectionComponent']:
        return await super().get(entity_id, repo)
