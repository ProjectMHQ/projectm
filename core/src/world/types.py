import enum


@enum.unique
class Direction(enum.IntEnum):
    NORTH = 0
    SOUTH = 1
    WEST = 2
    EAST = 3


@enum.unique
class Bit(enum.IntEnum):
    OFF = 0
    ON = 1


@enum.unique
class TerrainEnum(enum.IntEnum):
    NULL = 0
    WALL_OF_BRICKS = 1
    PATH = 2
