import typing

from core.src.world.components import ComponentType
from core.src.world.components.types import ComponentTypeEnum


class ConnectionComponent(ComponentType):
    key = ComponentTypeEnum.CONNECTION.value
    component_type = str

    def __init__(self, value: str):
        super().__init__(value)

    @property
    def value(self) -> typing.Optional[str]:
        return self._value

    @classmethod
    def get(cls, entity_id: int, repo=None) -> typing.Optional['ConnectionComponent']:
        return super().get(entity_id, repo)
