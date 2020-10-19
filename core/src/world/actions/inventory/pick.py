from core.src.auth.logging_factory import LOGGER
from core.src.world.components.factory import COLLECTIBLE_COMPONENTS
from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.inventory import InventoryComponent
from core.src.world.components.parent_of import ParentOfComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.entity import Entity
from core.src.world.utils.entity_utils import get_entity_id_from_raw_data_input, get_index_from_text


def get_pick_at_no_target_to_msg(target):
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "pick",
            "target": target,
            "status": "failure",
            "reason": "not_found"
        },
        'msg'
    )


def get_pick_at_not_collectible_target_msg(target):
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "pick",
            "target": target,
            "status": "failure",
            "reason": "not_collectible"
        },
        'msg'
    )


def get_pick_msg(target):
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "pick",
            "target": target,
            "status": "success"
        },
        'msg'
    )


async def pick(entity: Entity, *targets):
    from core.src.world.builder import world_repository, map_repository
    from core.src.world.builder import events_publisher_service

    if len(targets) > 1:
        await entity.emit_msg('Command error - Multi targets not implemented yet')
        return
    data = await world_repository.get_components_values_by_entities(
        [entity],
        [PosComponent, AttributesComponent]
    )
    pos = PosComponent(data[entity.entity_id][PosComponent.component_enum])
    room = await map_repository.get_room(pos)
    if not room.has_entities:
        await entity.emit_msg(get_pick_at_no_target_to_msg(targets[0]))
        return
    try:
        await room.populate_content(entity)
        totals, raw_room_content = await world_repository.get_raw_content_for_room_interaction(
            entity.entity_id, room
        )
        index, target = get_index_from_text(targets[0])
        found_entity = get_entity_id_from_raw_data_input(target, raw_room_content, index=index)
        if not found_entity:
            await entity.emit_msg(get_pick_at_no_target_to_msg(targets[0]))
            return
        else:
            entity_id, entity_keyword = found_entity
        res = await world_repository.check_entity_id_has_components(entity_id, *COLLECTIBLE_COMPONENTS)
        if not any(res):
            await entity.emit_msg(get_pick_at_not_collectible_target_msg(entity_keyword))
            return

        picked_entity = Entity(entity_id)\
            .add_bound(pos)\
            .set(PosComponent().add_previous_position(pos))\
            .set(ParentOfComponent(entity.entity_id))
        entity.set(InventoryComponent().add(entity_id))
        await world_repository.update_entities(picked_entity, entity)

        action = {'action': 'pick'}
        await events_publisher_service.on_entity_do_public_action(entity, pos, action, entity_id)

        await entity.emit_msg(get_pick_msg(entity_keyword))
        await entity.emit_system_event(
            {
                "event": "pick",
                "target": "entity",
                "details": {
                    "title": entity_keyword
                }
            }
        )
    except Exception as e:
        LOGGER.core.exception('log exception')
        raise e
