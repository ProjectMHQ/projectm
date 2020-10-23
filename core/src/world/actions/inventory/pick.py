from core.src.world.actions.inventory.inventory_messages import InventoryMessages
from core.src.world.components.collectible import CollectibleComponent
from core.src.world.components.inventory import InventoryComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.entity import Entity
from core.src.world.utils.entity_utils import update_entities, search_entities_in_room_by_keyword, \
    move_entity_from_container, load_components, search_entities_in_container_by_keyword, \
    search_entity_in_sight_by_keyword
from core.src.world.utils.messaging import emit_msg, get_stacker, emit_room_sys_msg, emit_room_msg, emit_sys_msg
from core.src.world.utils.world_utils import get_current_room

messages = InventoryMessages()


async def pick(entity: Entity, *arguments):
    keyword = arguments[0]
    if len(arguments) == 1:
        room = await get_current_room(entity)
        items_to_pick = await search_entities_in_room_by_keyword(
            room, keyword, filter_by=CollectibleComponent(True)
        )
        container_entity = None
    elif len(arguments) == 2:
        container_keyword = arguments[1]
        container_entity = await search_entity_in_sight_by_keyword(
            entity, container_keyword, filter_by=InventoryComponent, include_self=False
        )
        await load_components(container_entity, InventoryComponent)
        if not container_entity:
            await emit_msg(entity, messages.target_not_in_room())
            return
        container_inventory = container_entity.get_component(InventoryComponent)
        items_to_pick = await search_entities_in_container_by_keyword(container_inventory, keyword)
    else:
        raise ValueError('max 2 arguments')
    if not items_to_pick:
        await emit_msg(entity, messages.target_not_in_room())
        return

    await load_components(entity, InventoryComponent)
    inventory = entity.get_component(InventoryComponent)
    position = entity.get_component(PosComponent)
    for item in items_to_pick:
        move_entity_from_container(item, target=inventory, current_position=position, parent=container_entity)
    msgs_stack = get_stacker()
    if len(items_to_pick) == 1:
        if container_entity:
            # SINGLE ITEM FOUND IN CONTAINER
            msgs_stack.add(
                emit_msg(entity, messages.item_picked_from_container(items_to_pick[0], container_entity)),
                emit_room_msg(
                    origin=entity,
                    message_template=messages.entity_picked_item_from_container(items_to_pick[0], container_entity)
                ),
            )
        else:
            # SINGLE ITEM FOUND IN ROOM
            msgs_stack.add(
                emit_msg(entity, messages.item_picked(items_to_pick[0])),
                emit_room_msg(origin=entity, message_template=messages.entity_picked_item(items_to_pick[0])),
            )
    else:
        if container_entity:
            # MULTIPLE ITEMS FOUND IN CONTAINER
            msgs_stack.add(
                emit_msg(entity, messages.picked_multiple_items_from_container(container_entity)),
                emit_room_msg(
                    origin=entity,
                    message_template=messages.entity_picked_multiple_items_from_container(container_entity)
                ),
            )
        else:
            # MULTIPLE ITEMS FOUND IN ROOM
            msgs_stack.add(
                emit_msg(entity, messages.picked_multiple_items()),
                emit_room_msg(origin=entity, message_template=messages.entity_picked_multiple_items()),
            )
    if items_to_pick:
        msgs_stack.add(
            emit_sys_msg(entity, 'add_items', messages.items_to_message(items_to_pick)),
        )
        if not container_entity:
            msgs_stack.add(emit_room_sys_msg(entity, 'remove_items', messages.items_to_message(items_to_pick)))
        if not await update_entities(
                entity,
                *items_to_pick,
                *(container_entity and (container_entity, ) or ())
        ):
            await emit_msg(entity, messages.cannot_pick_item())
            msgs_stack.cancel()
        else:
            await msgs_stack.execute()
