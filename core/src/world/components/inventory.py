import json
import typing

from core.src.world.components import ComponentType
from core.src.world.components._types_ import ComponentTypeEnum


class InventoryComponent(ComponentType):
    component_enum = ComponentTypeEnum.INVENTORY
    key = ComponentTypeEnum.INVENTORY.value
    component_type = list
    libname = "inventory"
    subtype = int

    def __init__(self, value: (list, tuple) = None):
        self._to_remove = []
        self._to_add = []
        if value != list:
            if value is None:
                value = []
            value = list(value)
        super().__init__(value)
        self._populated = []
        self._raw_populated = []
        self._bounded_items = []

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
        for x in entity_ids:
            assert isinstance(x, int)
        self._to_add.extend(list(entity_ids))
        return self

    def remove(self, *entity_ids):
        for x in entity_ids:
            assert isinstance(x, int)
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

    async def populate(self, *components, repo=None):
        from core.src.world.domain.entity import Entity
        if not repo:
            from core.src.world.builder import world_repository
            repo = world_repository
        data = await repo.get_components_values_by_entities([Entity(x) for x in self.content], list(components))
        self._raw_populated = data
        self._populated = [data[x] for x in self.content]
        return self

    def get_items_from_attributes(self, key: str, value: str):
        from core.src.world.components.attributes import AttributesComponent
        from core.src.world.domain.entity import Entity
        if '*' not in value:
            for i, v in enumerate(self._populated):
                if v[AttributesComponent.component_enum][key].startswith(value):
                    return [Entity(entity_id=self.content[i])]
        else:
            res = []
            assert value[-1] == '*'
            value = value.replace('*', '')
            for i, v in enumerate(self._populated):
                if v[AttributesComponent.component_enum][key].startswith(value):
                    res.append(Entity(entity_id=self.content[i]))
            return res

    def get_item_component(self, entity_id: int, component: typing.Type[ComponentType]):
        return component(self._raw_populated[entity_id][component.component_enum])

    def is_active(self):
        return True

    @classmethod
    def is_array(cls):
        return True

    @classmethod
    def from_bytes(cls, value: bytes):
        return value and cls(json.loads(value)) or []

    def add_bounded_item_id(self, item_id: int):
        self._bounded_items.append(item_id)
        return self

    def clear_bounds(self):
        self._bounded_items = []

    @property
    def bounds(self):
        return self._bounded_items
