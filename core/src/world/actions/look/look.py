from core.src.world.actions.look.messages import LookMessages
from core.src.world.components.attributes import AttributesComponent
from core.src.world.domain.entity import Entity
from core.src.world.utils.entity_utils import search_entity_in_sight_by_keyword, ensure_same_position
from core.src.world.utils.messaging import emit_sys_msg, emit_msg, emit_room_msg, check_entity_can_receive_messages
from core.src.world.utils.world_types import DirectionEnum
from core.src.world.utils.world_utils import get_direction, get_current_room, get_room_at_direction

messages = LookMessages()


async def look(entity: Entity, *arguments: str):
    if not arguments:
        room = await get_current_room(entity)
        await emit_sys_msg(entity, "look", room)
    elif len(arguments) == 1 and get_direction(arguments[0]):
        await look_at_direction(entity, get_direction(arguments[0]))
    else:
        await look_at_target(entity, *arguments)


async def look_at_direction(entity: Entity, direction: DirectionEnum):
    room = await get_room_at_direction(entity, direction)
    await emit_msg(entity, messages.look_at_direction(direction))
    await emit_sys_msg(entity, "look", room)


async def look_at_target(entity: Entity, *arguments: str):
    if len(arguments) > 1:
        await emit_msg(entity, 'Command error - Nested targets not implemented yet')
        return
    target_entity = await search_entity_in_sight_by_keyword(entity, arguments[0])
    if not target_entity:
        await emit_msg(entity, messages.missing_target())
    elif entity.entity_id == target_entity.entity_id:
        await emit_msg(entity, messages.self_look())
    elif not await ensure_same_position(entity, target_entity):
        await emit_msg(entity, messages.missing_target())
    else:
        if await check_entity_can_receive_messages(target_entity):
            # Avoid to send messages to... knives, for example :-)
            await emit_msg(
                target_entity,
                messages.entity_looks_at_you(entity.get_component(AttributesComponent).keyword)
            )

        await emit_room_msg(
            origin=entity,
            target=target_entity,
            message_template=messages.entity_looks_at_entity_template()
        )
        await emit_msg(entity, messages.look_at_entity(target_entity.get_component(AttributesComponent).keyword)),
        await emit_sys_msg(entity, "look", target_entity)
