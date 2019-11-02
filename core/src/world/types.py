import enum
import typing

Pos = typing.NamedTuple(
    'Pos',
    (
        ('x', int),
        ('y', int),
        ('z', typing.Optional[int])
    )
)


@enum.unique
class Direction(enum.IntEnum):
    NORTH = 0
    SOUTH = 1
    WEST = 2
    EAST = 3
