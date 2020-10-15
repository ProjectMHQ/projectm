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
    pending = []
    for item in items:
        item.set(pos)
        item.set(ParentOfComponent())
        inventory.remove(item.entity_id)
        attributes = inventory.get_item_component(item.entity_id, AttributesComponent)
        pending.append(entity.emit_msg(get_drop_msg(attributes.name)))
        pending.append(
            events_publisher_service.on_entity_do_public_action(entity, pos, {'action': 'drop'}, item.entity_id)
        )
        pending.append(entity.emit_system_event(
            {
                "event": "drop",
                "target": "entity",
                "details": {
                    "title": attributes.name
                }
            }
        )
        )
    entity.set(inventory)
    await world_repository.update_entities(entity, *items)
    await asyncio.gather(*pending)

