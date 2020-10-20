import typing

from core.src.world.components import ComponentType
from core.src.world.components._types_ import ComponentTypeEnum


class CollectibleComponent(ComponentType):
    component_enum = ComponentTypeEnum.COLLECTIBLE
    key = ComponentTypeEnum.COLLECTIBLE.value
    component_type = bool
    libname = "collectible"
    has_default = True

    def __init__(self, value: (int, bool) = None):
        if not isinstance(value, bool):
            assert value in (0, 1), value
            value = bool(value or 0)
        super().__init__(value)

    @property
    def value(self) -> bool:
        return self._value

    @classmethod
    async def get(cls, entity_id: bool, repo=None) -> typing.Optional['CollectibleComponent']:
        return await super().get(entity_id, repo)

    def as_int(self):
        return int(self._value)
