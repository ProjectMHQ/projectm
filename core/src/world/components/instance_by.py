import typing

from core.src.world.components import ComponentType
from core.src.world.components._types_ import ComponentTypeEnum


class InstanceByComponent(ComponentType):
    component_enum = ComponentTypeEnum.INSTANCE_BY
    key = ComponentTypeEnum.INSTANCE_BY.value
    component_type = int
    libname = "instance_by"

    def __init__(self, value: str):
        super().__init__(value)

    @property
    def value(self) -> typing.Optional[str]:
        return self._value

    @classmethod
    async def get(cls, entity_id: int, repo=None) -> typing.Optional['InstanceByComponent']:
        return await super().get(entity_id, repo)
