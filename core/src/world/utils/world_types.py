import enum

import typing


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
    GRASS = 3


Transport = typing.NamedTuple(
    'Transport',
    (
        ('namespace', str),
        ('transport', callable)
    )
)


def is_terrain_walkable(terrain_type: TerrainEnum):
    return {
        TerrainEnum.NULL: False,
        TerrainEnum.WALL_OF_BRICKS: False,
        TerrainEnum.PATH: True,
        TerrainEnum.GRASS: True
    }[terrain_type]


EvaluatedEntity = typing.NamedTuple(
    'EvaluatedEntity',
    (
        ('name', str),
        ('type', int),
        ('status', str),
        ('known', bool),
        ('excerpt', str)
    )
)
