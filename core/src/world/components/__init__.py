import abc
import json
import typing

from core.src.world.components._types_ import ComponentTypeEnum


class ComponentType(metaclass=abc.ABCMeta):
    component_enum = ComponentTypeEnum.NULL
    key = ComponentTypeEnum.NULL.value
    component_type = NotImplementedError

    def __init__(self, value):
        self._value = value
        self._component_values = set()

    @abc.abstractmethod
    def value(self):
        pass  # pragma: no cover

    @classmethod
    async def get(cls, entity_id: int, repo=None) -> typing.Optional['ComponentType']:
        if not repo:
            from core.src.world.builder import world_repository as repo
        data = await repo.get_components_values_per_entity(entity_id, cls)
        return data and cls(cls.cast_type(data))

    def is_active(self):
        return bool(self.value)

    def has_data(self):
        return self.component_type != bool

    def has_operation(self):
        return False

    @classmethod
    def cast_type(cls, data: bytes):
        if cls.component_type == str:
            return data and data.decode() or None
        elif cls.component_type == bool:
            return bool(data)
        elif cls.component_type == list:
            return data and json.loads(data.decode()) or None
        elif cls.component_type == dict:
            return data and json.loads(data.decode()) or None
        return data is not None and cls.component_type(data)

    @property
    def serialized(self):
        return self.value

    def add_component_value(self, key: str, value: (bool, int, str)):
        if self.component_type != dict:
            raise NotImplementedError
        assert key not in self._value, key
        assert key in self._component_values, (key, self._component_values)
        assert isinstance(value, (int, str, bool))
        self._value[key] = value
