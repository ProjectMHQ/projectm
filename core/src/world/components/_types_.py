import enum


@enum.unique
class ComponentTypeEnum(enum.IntEnum):
    """
    enumerate components here to avoid mistakes on duplicates keys.
    """
    NULL = 0
    CREATED_AT = 1
    CONNECTION = 2
    POS = 3
    CHARACTER = 4
    WEAPON = 5
    HAND = 6
    ATTRIBUTES = 7
    INSTANCE_OF = 8
