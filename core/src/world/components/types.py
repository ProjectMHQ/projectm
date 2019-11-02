import enum


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
