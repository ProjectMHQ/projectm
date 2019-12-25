import asyncio

from core.src.world import exceptions
from core.src.world.actions.utils.utils import DirectionEnum, direction_to_coords_delta, apply_delta_to_position
from core.src.world.actions_scheduler.tools import singleton_action, cancellable_scheduled_action_factory
from core.src.world.actions.cast import cast_entity
from core.src.world.actions.getmap import getmap
from core.src.world.actions.look import look
from core.src.world.components.pos import PosComponent
from core.src.world.domain.room import RoomPosition
from core.src.world.entity import Entity


def get_broadcast_msg_movement(status, direction):
    return {
        "a": "movement",
        "st": status,
        "d": direction.value,
        "sp": 1
    }


def get_movement_message_no_walkable_direction(d) -> str:
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "move",
            "status": "error",
            "direction": "{}".format(d.value),
            "code": "terrain"
        },
        'msg'
    )


def get_movement_message_payload(d, status) -> str:
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "move",
            "status": status,
            "direction": "{}".format(d.value),
            "speed": 1
        },
        'msg'
    )


@singleton_action
async def move_entity(entity: Entity, direction: str):
    from core.src.world.builder import world_repository, map_repository, singleton_actions_scheduler
    direction = DirectionEnum(direction.lower())
    pos = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
    delta = direction_to_coords_delta(direction)
    where = apply_delta_to_position(RoomPosition(pos.x, pos.y, pos.z), delta)
    try:
        room = await map_repository.get_room(where)
    except exceptions.RoomError:
        room = None

    if not room:
        await entity.emit_msg(get_movement_message_no_walkable_direction(direction))
        return

    if not await room.walkable_by(entity):
        await entity.emit_msg(get_movement_message_no_walkable_direction(direction))
        return

    await entity.emit_msg(get_movement_message_payload(direction, "begin"))

    await singleton_actions_scheduler.schedule(
        cancellable_scheduled_action_factory(
            entity,
            ScheduledMovement(entity, direction, pos),
            wait_for=speed_component_to_movement_waiting_time(0.01)
        )
    )
move_entity.get_self = True


async def do_move_entity(entity, position, direction, reason, emit_msg=True):
    emit_msg and await entity.emit_msg(get_movement_message_payload(direction, "success"))
    await cast_entity(entity, position, reason=reason)
    await asyncio.gather(
        getmap(entity),
        look(entity)
    )


class ScheduledMovement:
    def __init__(self, entity: Entity, direction: DirectionEnum, current_position):
        self.entity = entity
        self.direction = direction
        self.pos = current_position

    async def do(self) -> bool:
        delta = direction_to_coords_delta(self.direction)
        where = apply_delta_to_position(RoomPosition(self.pos.x, self.pos.y, self.pos.z), delta)
        from core.src.world.builder import map_repository
        try:
            room = await map_repository.get_room(where)
        except exceptions.RoomError:
            room = None

        if not await room.walkable_by(self.entity):
            await self.entity.emit_msg(get_movement_message_no_walkable_direction(self.direction))
            return False

        await do_move_entity(
            self.entity,
            PosComponent([where.x, where.y, where.z]),
            self.direction,
            "movement"
        )
        self.pos = where
        return True

    async def stop(self):
        pass

    async def impossible(self):
        pass


def speed_component_to_movement_waiting_time(entity):
    return entity
