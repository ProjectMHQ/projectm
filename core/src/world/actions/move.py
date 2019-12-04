import asyncio
import enum

import typing

from core.src.world import exceptions
from core.src.world.actions import singleton_action
from core.src.world.actions.cast import cast_entity
from core.src.world.actions.getmap import getmap
from core.src.world.actions.look import look
from core.src.world.actions_scheduler.scheduled_actions_factories import cancellable_scheduled_action_factory
from core.src.world.builder import world_repository, map_repository, events_publisher_service
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


def get_broadcast_msg_movement(status, direction):
    return {
        "a": "movement",
        "st": status,
        "d": direction.value,
        "sp": 1
    }


def get_msg_no_walkable(d):
    return {
        "event": "move",
        "status": "error",
        "direction": "{}".format(d.value),
        "code": "terrain"
    }


def get_msg_movement(d, status):
    return {
        "event": "move",
        "status": status,
        "direction": "{}".format(d.value),
        "speed": 1
    }


def direction_to_coords_delta(direction: DirectionEnum) -> typing.Tuple:
    return {
        DirectionEnum.NORTH: (0, 1, 0),
        DirectionEnum.SOUTH: (0, -1, 0),
        DirectionEnum.EAST: (1, 0, 0),
        DirectionEnum.WEST: (-1, 0, 0),
        DirectionEnum.UP: (0, 0, 1),
        DirectionEnum.DOWN: (0, 0, -1),
    }[direction]


def apply_delta_to_room_position(room_position: RoomPosition, delta: typing.Tuple[int, int, int]):
    return RoomPosition(
        x=room_position.x + delta[0],
        y=room_position.y + delta[1],
        z=room_position.z + delta[2],
    )


@singleton_action
async def move_entity(entity: Entity, direction: str):
    direction = DirectionEnum(direction.lower())
    pos = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
    delta = direction_to_coords_delta(direction)
    where = apply_delta_to_room_position(RoomPosition(pos.x, pos.y, pos.z), delta)
    try:
        room = await map_repository.get_room(where)
    except exceptions.RoomError:
        room = None

    if not room:
        await entity.emit_msg(get_msg_no_walkable(direction))
        return

    if not await room.walkable_by(entity):
        await entity.emit_msg(get_msg_no_walkable(direction))
        return
    await events_publisher_service.on_entity_do_public_action(
        entity,
        pos,
        get_broadcast_msg_movement("begin", direction)
    )
    await entity.emit_msg(get_msg_movement(direction, "begin"))

    from core.src.world.run_worker import singleton_actions_scheduler
    await singleton_actions_scheduler.schedule(
        cancellable_scheduled_action_factory(
            entity,
            ScheduledMovement(entity, direction, where),
            wait_for=speed_component_to_movement_waiting_time(0.01)
        )
    )
move_entity.get_self = True


class ScheduledMovement:
    def __init__(self, entity: Entity, direction: DirectionEnum, where: RoomPosition):
        self.entity = entity
        self.direction = direction
        self.where = where

    async def do(self):
        try:
            room = await map_repository.get_room(self.where)
        except exceptions.RoomError:
            room = None

        if not await room.walkable_by(self.entity):
            await self.entity.emit_msg(get_msg_no_walkable(self.direction))
            #await events_publisher_service.on_entity_do_public_action(
            #    self.entity,
            #    room.position,
            #    get_broadcast_msg_movement("canceled", self.direction)
            #)
            return

        await self.entity.emit_msg(get_msg_movement(self.direction, "success"))
        #await events_publisher_service.on_entity_do_public_action(
        #    self.entity,
        #    room.position,
        #    get_broadcast_msg_movement("success", self.direction)
        #)
        await cast_entity(self.entity, PosComponent([self.where.x, self.where.y, self.where.z]))
        await asyncio.gather(
            getmap(self.entity),
            look(self.entity)
        )


    async def stop(self):
        #await events_publisher_service.on_entity_do_public_action(
        #    self.entity,
        #    await world_repository.get_component_value_by_entity_id(self.entity.entity_id, PosComponent),
        #    get_broadcast_msg_movement("canceled", self.direction)
        #)
        pass

    async def impossible(self):
        pass


def speed_component_to_movement_waiting_time(entity):
    # FIXME TODO
    return entity
