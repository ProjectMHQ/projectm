from core.src.world.actions.inventory.inventory_messages import InventoryMessages
from core.src.world.components.inventory import InventoryComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.entity import Entity
from core.src.world.utils.entity_utils import load_components, update_entities, \
    search_entities_in_container_by_keyword, move_entity_from_container, search_entity_in_sight_by_keyword
from core.src.world.utils.messaging import emit_msg, emit_room_msg, emit_sys_msg, get_stacker

messages = InventoryMessages()


async def put(entity: Entity, keyword: str, target: str):
    await load_components(entity, PosComponent, InventoryComponent)
    inventory = entity.get_component(InventoryComponent)
    items = await search_entities_in_container_by_keyword(inventory, keyword)
    target_entity = await search_entity_in_sight_by_keyword(
        entity, target, filter_by=InventoryComponent, include_self=False
    )
    if not target_entity:
        await emit_msg(entity, messages.target_not_found())
        return
    msgs_stack = get_stacker()
    items_to_drop = []
    for item in items:
        items_to_drop.append(
            move_entity_from_container(
                item,
                target=target_entity.get_component(InventoryComponent),
                parent=entity
            )
        )
    if not items_to_drop:
        await emit_msg(entity, messages.target_not_found())
        return
    msgs_stack.add(
        emit_sys_msg(entity, 'remove_items', messages.items_to_message(items_to_drop)),
        #emit_room_sys_msg(entity, 'add_items', messages.items_to_message(items_to_drop)) # todo event for container
    )
    if len(items_to_drop) == 1:
        msgs_stack.add(
            emit_msg(entity, messages.on_put_item(items[0], target_entity)),
            emit_room_msg(origin=entity, message_template=messages.on_entity_put_item(items[0], target_entity))
        )
    else:
        msgs_stack.add(
            emit_msg(entity, messages.on_put_multiple_items(target_entity)),
            emit_room_msg(origin=entity, message_template=messages.on_entity_put_multiple_items(target_entity))
        )
    if not await update_entities(entity, target_entity, *items_to_drop):
        await emit_msg(entity, messages.target_not_found())
        msgs_stack.cancel()
    else:
        await msgs_stack.execute()
