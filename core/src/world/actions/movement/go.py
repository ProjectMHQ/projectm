from core.src.world.actions.movement.move import speed_component_to_movement_waiting_time
from core.src.world.actions.movement.movement_messages import MovementMessages
from core.src.world.actions.movement.schedules import ScheduledMovement
from core.src.world.utils.messaging import emit_msg, emit_room_msg
from core.src.world.actions_scheduler.tools import singleton_action, looped_cancellable_scheduled_action_factory
from core.src.world.domain.entity import Entity
from core.src.world.utils.world_utils import get_direction, get_room_at_direction

messages = MovementMessages()


@singleton_action
async def go_entity(entity: Entity, direction: str):
    direction = get_direction(direction)
    if not direction:
        await emit_msg(entity, messages.not_recognized_direction())
        return
    target_room = await get_room_at_direction(entity, direction, populate=False)
    if not target_room:
        await emit_msg(entity, messages.invalid_direction())
        return

    if not await target_room.walkable_by(entity):
        await emit_msg(entity, messages.invalid_direction())
        return

    await emit_msg(entity, messages.movement_begins(direction))
    await emit_room_msg(
        origin=entity,
        message_template=messages.entity_begin_movement_template(direction)
    )
    action = looped_cancellable_scheduled_action_factory(
        entity,
        ScheduledMovement(entity, direction, target_room, escape_corners=True),
        wait_for=speed_component_to_movement_waiting_time(1)
    )
    await go_entity.schedule(action)
