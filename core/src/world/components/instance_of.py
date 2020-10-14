import typing

from core.src.world.components import ComponentType
from core.src.world.components._types_ import ComponentTypeEnum


class InstanceOfComponent(ComponentType):
    component_enum = ComponentTypeEnum.INSTANCE_OF
    key = ComponentTypeEnum.INSTANCE_OF.value
    component_type = str
    libname = "instance_of"

    def __init__(self, value: str):
        super().__init__(value)

    @property
    def value(self) -> typing.Optional[str]:
        return self._value

    @classmethod
    async def get(cls, entity_id: int, repo=None) -> typing.Optional['InstanceOfComponent']:
        return await super().get(entity_id, repo)
