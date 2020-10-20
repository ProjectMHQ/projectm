from core.src.world.actions.inventory.inventory_messages import InventoryMessages
from core.src.world.components.collectible import CollectibleComponent
from core.src.world.domain.entity import Entity
from core.src.world.utils.entity_utils import update_entities, search_entities_in_room_by_keyword
from core.src.world.utils.messaging import emit_msg, get_stacker, emit_room_sys_msg, emit_room_msg, emit_sys_msg
from core.src.world.utils.world_utils import get_current_room

messages = InventoryMessages()


async def pick(entity: Entity, *arguments):
    if len(arguments) > 1:
        await emit_msg(entity, 'Command error - Nested targets not implemented yet')
        return
    keyword = arguments[0]
    room = await get_current_room(entity)
    if not room.has_entities:
        await entity.emit_msg(messages.target_not_in_room())
        return
    items = search_entities_in_room_by_keyword(room, keyword, filter_by=CollectibleComponent(True))
    if not items:
        await entity.emit_msg(messages.target_not_in_room())
        return
    items_to_pick = []
    for item in items_to_pick:
        items_to_pick.append(item)
    msgs_stack = get_stacker()
    if len(items_to_pick) == 1:
        msgs_stack.add(
            emit_msg(entity, messages.item_picked(items_to_pick[0])),
            emit_room_msg(origin=entity, message_template=messages.entity_picked_item(items_to_pick[0])),
        )
    else:
        msgs_stack.add(
            emit_msg(entity, messages.picked_multiple_items()),
            emit_room_msg(origin=entity, message_template=messages.entity_picked_multiple_items()),
        )
    if items_to_pick:
        msgs_stack.add(
            emit_sys_msg(entity, 'add_items', messages.items_to_message(items_to_pick)),
            emit_room_sys_msg(entity, 'remove_items', messages.items_to_message(items_to_pick))
        )

    if not update_entities(entity, *items_to_pick):
        await entity.emit_msg(messages.cannot_pick_item())
        msgs_stack.cancel()
    else:
        await msgs_stack.execute()
