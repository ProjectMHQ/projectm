import asyncio

from core.src.world.actions.look.messages import LookMessages
from core.src.world.actions.movement._utils_ import DirectionEnum
from core.src.world.domain.entity import Entity
from core.src.world.utils.utils import get_action_target
from core.src.world.utils.entity_utils import search_entity_by_keyword, get_current_room, get_room_at_direction
from core.src.world.utils.messaging import emit_system_message, emit_msg, emit_room_msg

messages = LookMessages()


async def look(entity: Entity, *targets):
    if not targets:
        room = await get_current_room(entity)
        await room.populate_room_content_for_look(entity)
        await emit_system_message(entity, "look", room)
    elif len(targets) == 1 and targets[0] in (x.value for x in DirectionEnum):
        await look_at_direction(entity, targets)
    else:
        await look_at_target(entity, *targets)


async def look_at_direction(entity, targets):
    direction = targets[0]
    assert direction not in ('u', 'd'), 'not supported yet'
    room = await get_room_at_direction(entity, DirectionEnum(direction))
    await room.populate_room_content_for_look(entity)
    await asyncio.gather(
        emit_msg(entity, messages.look_at_direction(DirectionEnum(direction))),
        emit_system_message(entity, "look", room)
    )


async def look_at_target(entity, *targets):
    if len(targets) > 1:
        await entity.emit_msg('Command error - Multi targets not implemented yet')
        return
    keyword = targets[0]
    search_response = await search_entity_by_keyword(entity, keyword)
    if not search_response:
        await emit_msg(entity, messages.missing_target())
    target = await get_action_target(search_response)
    if not target:
        await emit_msg(entity, messages.missing_target())
    elif entity.entity_id == search_response.entity_id:
        await emit_msg(entity, messages.self_look())
    else:
        await asyncio.gather(
            emit_msg(target, messages.entity_looks_at_you(target.components.attributes.keyword)),
            emit_room_msg(
                room=search_response.room,
                origin_attributes=search_response.search_origin_attributes,
                action_target=target,
                message_template=messages.entity_looks_at_entity_template()
            ),
            emit_msg(entity, messages.look_at_entity(search_response.keyword)),
            emit_system_message(entity, "look", target)
        )
