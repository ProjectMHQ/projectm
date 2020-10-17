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

EvaluatedEntity = typing.NamedTuple(
    'EvaluatedEntity',
    (
        ('name', str),
        ('type', int),
        ('status', int),
        ('known', bool),
        ('excerpt', str),
        ('entity_id', int)
    )
)


class DirectionEnum(enum.Enum):
    NORTH = 'n'
    SOUTH = 's'
    EAST = 'e'
    WEST = 'w'
    UP = 'u'
    DOWN = 'd'
