import abc
import typing

from core.src.world.components.types import ComponentTypeEnum


class ComponentType(metaclass=abc.ABCMeta):
    component_enum = ComponentTypeEnum.NULL
    key = ComponentTypeEnum.NULL.value
    component_type = NotImplementedError

    def __init__(self, value):
        self._value = value

    @abc.abstractmethod
    def value(self):
        pass  # pragma: no cover

    @classmethod
    def get(cls, entity_id: int, repo=None) -> typing.Optional['ComponentType']:
        if not repo:
            from core.src.world.builder import world_repository as repo
        data = repo.get_components_values_per_entity(entity_id, cls)
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
            return data.decode()
        return cls.component_type(data)
