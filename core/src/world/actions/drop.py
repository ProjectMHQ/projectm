import asyncio

from core.src.world.components.inventory import InventoryComponent
from core.src.world.components.parent_of import ParentOfComponent
from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.entity import Entity


def get_drop_at_no_target_to_msg(target):
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "drop",
            "target": target,
            "status": "failure",
            "reason": "not_found"
        },
        'msg'
    )


def get_drop_at_not_collectible_target_msg(target):
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "drop",
            "target": target,
            "status": "failure",
            "reason": "not_collectible"
        },
        'msg'
    )


def get_drop_msg(target):
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "drop",
            "target": target,
            "status": "success"
        },
        'msg'
    )


async def drop(entity: Entity, *targets):
    from core.src.world.builder import world_repository
    from core.src.world.builder import events_publisher_service

    if len(targets) > 1:
        await entity.emit_msg('Command error - Multi targets not implemented yet')
        return
    data = await world_repository.get_components_values_by_components(
        [entity.entity_id],
        [PosComponent, InventoryComponent]
    )
    pos = PosComponent(data[PosComponent.component_enum][entity.entity_id])
    inventory = InventoryComponent(data[InventoryComponent.component_enum][entity.entity_id])
    await inventory.populate(AttributesComponent)
    items = inventory.get_items_from_attributes('keyword', targets[0])
    futures = []
    bounded_inventory = InventoryComponent()
    for item in items:
        item.set(pos)
        item.set(ParentOfComponent())
        bounded_inventory.add_bounded_item_id(item.entity_id)
        inventory.remove(item.entity_id)
        attributes = inventory.get_item_component(item.entity_id, AttributesComponent)
        futures.append(entity.emit_msg(get_drop_msg(attributes.name)))
        futures.append(
            events_publisher_service.on_entity_do_public_action(entity, pos, {'action': 'drop'}, item.entity_id)
        )
        futures.append(entity.emit_system_event(
            {
                "event": "drop",
                "target": "entity",
                "details": {
                    "title": attributes.name
                }
            }
        )
        )
    entity.set(inventory).add_bound(bounded_inventory)
    response = await world_repository.update_entities(entity, *items)
    if response:
        await asyncio.gather(*futures)
    else:
        raise ValueError(response)
        # TODO - Cancel baked futures

