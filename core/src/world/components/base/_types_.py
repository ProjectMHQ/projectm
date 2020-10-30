import enum


@enum.unique
class ComponentTypeEnum(enum.IntEnum):
    """
    enumerate components here to avoid mistakes on duplicates keys.
    """
    NULL = 0
    POS = 3
    WEAPON = 5
    INVENTORY = 6
    ATTRIBUTES = 7
    PARENT_OF = 9
    COLLECTIBLE = 11
    SYSTEM = 12
