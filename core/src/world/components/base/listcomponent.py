import json
import typing

from core.src.world.components.base import ComponentType


class ListComponent(ComponentType):
    """
    This list component is 1:1 on a redis SortedSet, so it doesn't allow duplicates, but keeps order.
    Since no checks are made, ensure the code doesn't add duplicates into this component.
    """
    component_enum = NotImplementedError
    key = NotImplementedError
    component_type = list
    libname = NotImplementedError
    subtype = NotImplementedError

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

    @property
    def populated(self):
        return self._populated

    def __str__(self):
        return ', '.join(self._value)

    @property
    def value(self) -> typing.List[int]:
        return self._value

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
        for entity_id in entity_ids:
            self.add_bounded_item_id(entity_id)
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
