import asyncio

from core.src.world.components.inventory import InventoryComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.entity import Entity
from core.src.world.utils.entity_utils import load_components
from core.src.world.utils.messaging import emit_msg, emit_room_msg, emit_sys_msg


async def drop(entity: Entity, *targets):
    from core.src.world.builder import world_repository
    if len(targets) > 1:
        await entity.emit_msg('Command error - Multi targets not implemented yet')
        return
    await load_components(entity, PosComponent, InventoryComponent)
    inventory = entity.get_component(InventoryComponent)
    items = inventory.search_by_keyword(targets[0])
    position = entity.get_component(PosComponent)
    items_to_drop = []
    for item in items:
        items_to_drop.append(inventory.move(item, position))
    if not items:
        await entity.emit_msg(messages.target_not_found())
    else:
        if world_repository.update_entities(entity, *items_to_drop):
            await asyncio.gather(
                emit_msg(entity, messages.on_drop_items(items_to_drop)),
                emit_room_msg(origin=entity, message_template=messages.on_entity_drop_items(items_to_drop)),
                emit_sys_msg(entity, 'inventory_remove', messages.remove_items_from_inventory(items_to_drop)),
                emit_room_sys_msg(entity, messages.add_items_to_room(items_to_drop))
            )
        else:
            await entity.emit_msg(messages.target_not_found())
