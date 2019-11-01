import abc
import typing

from core.src.world.components.types import ComponentTypeEnum


class ComponentType(metaclass=abc.ABCMeta):
    key = ComponentTypeEnum.NULL
    ctype = NotImplementedError

    def __init__(self, value):
        self._value = value

    @abc.abstractmethod
    def value(self):
        pass  # pragma: no cover

    @classmethod
    def get(cls, entity_id: int, repository=None) -> typing.Optional['ComponentType']:
        if not repository:
            from core.src.world.builder import world_components_repository as repository
        data = repository.get_component_value(entity_id, cls.key)
        return data and cls(cls.ctype(data))
