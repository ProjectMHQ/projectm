import typing
from core.src.world.components.types import ComponentType, ComponentTypeEnum


class NameComponent(ComponentType):
    key = ComponentTypeEnum.NAME.value

    def __init__(self, value: str):
        super().__init__(value)

    @property
    def value(self) -> str:
        return self._value

    @classmethod
    def get(cls, entity_id: int, repo=None) -> typing.Optional['NameComponent']:
        return super().get(entity_id, repo)
