import asyncio
import enum

import typing

from core.src.world.actions.cast import cast_entity
from core.src.world.actions.getmap import getmap
from core.src.world.actions.look import look
from core.src.world.builder import world_repository, map_repository
from core.src.world.components.pos import PosComponent
from core.src.world.domain.room import RoomPosition
from core.src.world.entity import Entity


class DirectionEnum(enum.Enum):
    NORTH = 'n'
    SOUTH = 's'
    EAST = 'e'
    WEST = 'w'
    UP = 'u'
    DOWN = 'd'


MSG_NO_WALKABLE = {
    "event": "move",
    "error": "invalid",
    "code": "no_walkable",
    "message": "You cannot go there"
}


def direction_to_coords_delta(direction: DirectionEnum) -> typing.Tuple:
    return {
        DirectionEnum.NORTH: (0, 1, 0),
        DirectionEnum.SOUTH: (0, -1, 0),
        DirectionEnum.EAST: (1, 0, 0),
        DirectionEnum.WEST: (-1, 1, 0),
        DirectionEnum.UP: (0, 0, 1),
        DirectionEnum.DOWN: (0, 0, -1),
    }[direction]


def apply_delta_to_room_position(room_position: RoomPosition, delta: typing.Tuple[int, int, int]):
    return RoomPosition(
        x=room_position.x + delta[0],
        y=room_position.y + delta[1],
        z=room_position.z + delta[2],
    )


async def move_entity(entity: Entity, direction: str):
    try:
        direction = DirectionEnum(direction.lower())
    except Exception:
        raise

    pos = world_repository.get_component_value_by_entity(entity.entity_id, PosComponent)
    delta = direction_to_coords_delta(direction)
    where = apply_delta_to_room_position(RoomPosition(pos.x, pos.y, pos.z), delta)
    room = await map_repository.get_room(where)
    if not room:
        await entity.emit_msg(
            {
                "event": "move",
                "error": "invalid",
                "code": "non_exists",
                "message": "Location does not exists"
            }
        )
        return
    if not await room.walkable_by(entity):
        await entity.emit_msg(MSG_NO_WALKABLE)
        return
    await entity.emit_msg(
        {
            "event": "move",
            "status": "begin",
            "message": "You begin to move to {}".format(direction.name.lower())
        }
    )
    await asyncio.sleep(1)
    room = await map_repository.get_room(where)
    if not await room.walkable_by(entity):
        entity.emit_msg(MSG_NO_WALKABLE)
        return
    await entity.emit_msg(
        {
            "event": "move",
            "status": "done",
            "message": "You move to {}".format(direction.name.lower())
        }
    )
    await cast_entity(entity, PosComponent([where.x, where.y, where.z]))
    await asyncio.gather(
        getmap(entity),
        look(entity)
    )

move_entity.get_self = True
