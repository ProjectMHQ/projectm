import enum


@enum.unique
class ComponentTypeEnum(enum.IntEnum):
    """
    enumerate components here to avoid mistakes on duplicates keys.
    """
    NULL = 0
    POSITION = 1
    SYSTEM = 2
    ATTRIBUTES = 3
    WEAPON = 4
    INVENTORY = 5
