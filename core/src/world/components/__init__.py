import abc
import typing

from core.src.world.components.types import ComponentTypeEnum


class ComponentType(metaclass=abc.ABCMeta):
    key = ComponentTypeEnum.NULL
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
        return data and cls(cls.component_type(data))

    def is_active(self):
        return bool(self.value)

    def has_data(self):
        return self.component_type != bool
