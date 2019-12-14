import itertools
from core.src.auth.logging_factory import LOGGER
from core.src.world.actions.look import get_look_at_no_target_to_msg
from core.src.world.actions_scheduler.tools import singleton_action
from core.src.world.builder import follow_system_manager
from core.src.world.components.name import NameComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.room import RoomPosition
from core.src.world.entity import Entity
from core.src.world.utils.entity_utils import get_entity_id_from_raw_data_input, get_index_from_text


def get_follow_no_target_to_msg():
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "follow",
            "target": "entity",
            "status": "failure",
            "reason": "not_found"
        },
        'msg'
    )


def get_follow_target_to_msg(target_alias):
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "follow",
            "action": "follow",
            "status": "success",
            "alias": target_alias,
        },
        'msg'
    )


def get_defollow_success():
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "follow",
            "action": "defollow",
            "status": "success",
        },
        'msg'
    )


@singleton_action
async def follow(
    entity: Entity,
    *target: str
):
    if not len(target):
        return await _handle_defollow(entity)
    elif len(target) > 1:
        return
    else:
        target = target[0]

    from core.src.world.builder import world_repository, map_repository
    data = await world_repository.get_components_values_by_entities(
        [entity],
        [PosComponent, NameComponent]
    )
    pos = PosComponent(data[entity.entity_id][PosComponent.component_enum])
    name_value = data[entity.entity_id][NameComponent.component_enum]
    room = await map_repository.get_room(RoomPosition(x=pos.x, y=pos.y, z=pos.z))
    if not room.has_entities:
        await entity.emit_msg(get_follow_no_target_to_msg())
        return
    try:
        await room.populate_room_content_for_look(entity)
        totals, raw_room_content = await world_repository.get_raw_content_for_room_interaction(entity.entity_id, room)
        raw_room_content = itertools.chain(
            raw_room_content,
            (x for x in [
                {'entity_id': entity.entity_id, 'data': [name_value, *('' for _ in range(1, totals))]}]
             )
        )
        index, target = get_index_from_text(target)
        entity_id = get_entity_id_from_raw_data_input(target, totals, raw_room_content, index=index)
        if not entity_id:
            await entity.emit_msg(get_look_at_no_target_to_msg())
            return
        if entity_id == entity.entity_id:
            await _handle_defollow(entity)
            return
        _handle_follow(entity, entity_id, target)
    except Exception as e:
        LOGGER.core.exception('log exception')
        raise e


async def _handle_defollow(entity):
    await follow_system_manager.stop_following(entity)


async def _handle_follow(entity: Entity, entity_id: int, target: str):
    await follow_system_manager.follow_entity(entity, entity_id)
