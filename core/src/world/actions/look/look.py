from core.src.world.actions.look.messages import LookMessages
from core.src.world.actions.movement._utils_ import DirectionEnum
from core.src.world.components.attributes import AttributesComponent
from core.src.world.domain.entity import Entity
from core.src.world.utils.entity_utils import search_entity_by_keyword, get_current_room, get_room_at_direction
from core.src.world.utils.messaging import emit_system_message, emit_msg, emit_room_msg

messages = LookMessages()


async def look(entity: Entity, *arguments):
    if not arguments:
        room = await get_current_room(entity)
        await room.populate_room_content_for_look(entity)
        await emit_system_message(entity, "look", room)
    elif len(arguments) == 1 and arguments[0] in (x.value for x in DirectionEnum):
        await look_at_direction(entity, arguments)
    else:
        await look_at_target(entity, *arguments)


async def look_at_direction(entity, targets):
    direction = targets[0]
    assert direction not in ('u', 'd'), 'not supported yet'
    room = await get_room_at_direction(entity, DirectionEnum(direction))
    await room.populate_room_content_for_look(entity)
    await emit_msg(entity, messages.look_at_direction(DirectionEnum(direction))),
    await emit_system_message(entity, "look", room)


async def look_at_target(entity, *arguments):
    if len(arguments) > 1:
        await entity.emit_msg('Command error - Multi targets not implemented yet')
        return
    target_entity = await search_entity_by_keyword(entity, arguments[0])
    if not target_entity:
        await emit_msg(entity, messages.missing_target())
    elif entity.entity_id == target_entity.entity_id:
        await emit_msg(entity, messages.self_look())
    else:
        if not await emit_msg(
            target_entity,
            messages.entity_looks_at_you(entity.get_component(AttributesComponent).keyword)
        ):
            await emit_msg(entity, messages.missing_target())
            return

        await emit_room_msg(
                origin=entity,
                target=target_entity,
                message_template=messages.entity_looks_at_entity_template()
            )
        await emit_msg(entity, messages.look_at_entity(target_entity.get_component(AttributesComponent).keyword)),
        await emit_system_message(entity, "look", target_entity)
