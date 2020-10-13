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
    CHARACTER = 5
    WEAPON = 6
    HAND = 7
    ATTRIBUTES = 8
    INSTANCE_OF = 9
