from core.src.world import exceptions
from core.src.world.actions.move import get_movement_message_no_walkable_direction, get_movement_message_payload, \
    ScheduledMovement, speed_component_to_movement_waiting_time
from core.src.world.actions.utils.utils import DirectionEnum, direction_to_coords_delta, apply_delta_to_position
from core.src.world.actions_scheduler.tools import singleton_action, looped_cancellable_scheduled_action_factory
from core.src.world.components.pos import PosComponent
from core.src.world.domain.room import RoomPosition
from core.src.world.entity import Entity


def get_invalid_go_direction_message(d) -> str:
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "move",
            "status": "error",
            "direction": "d",
            "code": "invalid_direction"
        },
        'msg'
    )


@singleton_action
async def go_entity(entity: Entity, direction: str):
    from core.src.world.builder import world_repository, map_repository, singleton_actions_scheduler
    try:
        direction = DirectionEnum(direction.lower())
    except ValueError:
        await entity.emit_msg(get_invalid_go_direction_message(direction))
        return

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
        looped_cancellable_scheduled_action_factory(
            entity,
            ScheduledMovement(entity, direction, where),
            wait_for=speed_component_to_movement_waiting_time(0.5)
        )
    )
