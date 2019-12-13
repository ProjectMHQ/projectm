import enum
import typing

from core.src.world.components.pos import PosComponent
from core.src.world.domain.room import RoomPosition


class DirectionEnum(enum.Enum):
    NORTH = 'n'
    SOUTH = 's'
    EAST = 'e'
    WEST = 'w'
    UP = 'u'
    DOWN = 'd'


def direction_to_coords_delta(direction: object) -> typing.Tuple:
    return {
        DirectionEnum.NORTH: (0, 1, 0),
        DirectionEnum.SOUTH: (0, -1, 0),
        DirectionEnum.EAST: (1, 0, 0),
        DirectionEnum.WEST: (-1, 0, 0),
        DirectionEnum.UP: (0, 0, 1),
        DirectionEnum.DOWN: (0, 0, -1),
    }[direction]


def apply_delta_to_position(room_position: (PosComponent, RoomPosition), delta: typing.Tuple[int, int, int]):
    if isinstance(room_position, RoomPosition):
        return RoomPosition(
            x=room_position.x + delta[0],
            y=room_position.y + delta[1],
            z=room_position.z + delta[2],
        )
    elif isinstance(room_position, PosComponent):
        return PosComponent([
            room_position.x + delta[0],
            room_position.y + delta[1],
            room_position.z + delta[2]
            ]
        )
    else:
        raise ValueError
