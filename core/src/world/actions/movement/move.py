from core.src.world.actions.movement.schedules import ScheduledMovement
from core.src.world.actions.movement.movement_messages import MovementMessages
from core.src.world.utils.messaging import emit_msg
from core.src.world.actions_scheduler.tools import singleton_action, cancellable_scheduled_action_factory
from core.src.world.actions.system.cast import cast_entity
from core.src.world.actions.system.getmap import getmap
from core.src.world.actions.look.look import look
from core.src.world.domain.entity import Entity
from core.src.world.utils.world_utils import get_room_at_direction, get_direction

messages = MovementMessages()


@singleton_action
async def move_entity(entity: Entity, *arguments):
    assert len(arguments) == 1
    direction = get_direction(arguments[0])
    target_room = await get_room_at_direction(entity, direction)
    if not target_room:
        await emit_msg(entity, messages.invalid_direction())
        return
    if not await target_room.walkable_by(entity):
        await emit_msg(entity, messages.invalid_direction())
        return
    await emit_msg(entity, messages.movement_begins(direction))
    action = cancellable_scheduled_action_factory(
        entity,
        ScheduledMovement(entity, direction, target_room),
        wait_for=speed_component_to_movement_waiting_time(0.05)
    )
    await move_entity.schedule(action)

move_entity.get_self = True


async def do_move_entity(entity, room, direction, reason, emit_message=True):
    if await cast_entity(entity, room.position, reason=reason):
        emit_message and await emit_msg(entity, messages.movement_success(direction))
        await getmap(entity)
        await look(entity)
        entity.set_room(room)


def speed_component_to_movement_waiting_time(entity):
    return entity
