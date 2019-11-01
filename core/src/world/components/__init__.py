import typing

from core.src.world.components.component import ComponentTypeEnum


class ComponentType:
    key = ComponentTypeEnum
    ctype = NotImplementedError

    def __init__(self, value):
        self._value = value

    @property
    def value(self):
        return self._value

    @classmethod
    def get(cls, entity_id: int, repository=None) -> typing.Optional['ComponentType']:
        if not repository:
            from core.src.world.builder import world_components_repository as repository
        data = repository.get_component_value(entity_id, cls.key)
        return data and cls(cls.ctype(data))
