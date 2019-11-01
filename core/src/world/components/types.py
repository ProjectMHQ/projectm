import enum


@enum.unique
class ComponentTypeEnum(enum.IntEnum):
    """
    enumerate components here to avoid mistakes on duplicates keys.
    """
    NULL = 0
    CREATED_AT = 1
    NAME = 3
    CONNECTION = 2
    POS = 3


class ComponentType:
    key = ComponentTypeEnum
    value = None
