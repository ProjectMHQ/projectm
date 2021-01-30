from core.src.world.actions.inventory.inventory_messages import InventoryMessages
from core.src.world.components.inventory import InventoryComponent
from core.src.world.components.position import PositionComponent
from core.src.world.domain.entity import Entity
from core.src.world.utils.entity_utils import load_components, update_entities, \
    search_entities_in_container_by_keyword, move_entity_from_container
from core.src.world.utils.messaging import emit_msg, emit_room_msg, emit_sys_msg, emit_room_sys_msg, \
    get_stacker

messages = InventoryMessages()


async def drop(entity: Entity, keyword: str):
    await load_components(entity, PositionComponent, InventoryComponent)
    inventory = entity.get_component(InventoryComponent)
    items = await search_entities_in_container_by_keyword(inventory, keyword)
    msgs_stack = get_stacker()
    items_to_drop = []
    for item in items:
        items_to_drop.append(
            move_entity_from_container(
                item,
                target=entity.get_component(PositionComponent),
                current_owner=entity
            )
        )
    if not items_to_drop:
        await emit_msg(entity, messages.target_not_found())
        return
    entity.set_for_update(inventory)
    msgs_stack.add(
        emit_sys_msg(entity, 'remove_items', messages.items_to_message(items_to_drop)),
        emit_room_sys_msg(entity, 'add_items', messages.items_to_message(items_to_drop))
    )
    if len(items_to_drop) == 1:
        msgs_stack.add(
            emit_msg(entity, messages.on_drop_item(items[0])),
            emit_room_msg(origin=entity, message_template=messages.on_entity_drop_item(items[0]))
        )
    else:
        msgs_stack.add(
            emit_msg(entity, messages.on_drop_multiple_items()),
            emit_room_msg(origin=entity, message_template=messages.on_entity_drops_multiple_items())
        )
    if not await update_entities(entity, *items_to_drop):
        await emit_msg(entity, messages.target_not_found())
        msgs_stack.cancel()
    else:
        await msgs_stack.execute()
