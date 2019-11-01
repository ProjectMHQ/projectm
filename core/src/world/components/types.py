import enum
import typing


@enum.unique
class ComponentTypeEnum(enum.IntEnum):
    """
    enumerate components here to avoid mistakes on duplicates keys.
    """
    NULL = 0
    CREATED_AT = 1
    NAME = 2
    CONNECTION = 3
    POS = 4


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
