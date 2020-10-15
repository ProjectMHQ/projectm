import json
import typing

from core.src.world.components import ComponentType
from core.src.world.components._types_ import ComponentTypeEnum


class InventoryComponent(ComponentType):
    component_enum = ComponentTypeEnum.INVENTORY
    key = ComponentTypeEnum.INVENTORY.value
    component_type = list
    libname = "inventory"

    def __init__(self, value: (list, tuple) = None):
        self._to_remove = []
        self._to_add = []
        if value != list:
            if value is None:
                value = []
            value = list(value)
        super().__init__(value)

    def __str__(self):
        return ', '.join(self._value)

    @property
    def value(self) -> typing.List[int]:
        return self._value

    @classmethod
    async def get(cls, entity_id: int, repo=None) -> typing.Optional['InventoryComponent']:
        if not repo:
            from core.src.world.builder import world_repository as repo
        return await repo.get_entity_position(entity_id)

    @property
    def serialized(self):
        return json.dumps(self.value)

    def as_tuple(self):
        return tuple(self.value)

    def add(self, *entity_ids):
        self._to_add.extend(list(entity_ids))
        return self

    def remove(self, *entity_ids):
        self._to_remove.extend(list(entity_ids))
        return self

    @property
    def content(self):
        return self._value

    @property
    def to_add(self):
        return self._to_add or []

    @property
    def to_remove(self):
        return self._to_remove or []
