import itertools

import typing

from core.src.auth.logging_factory import LOGGER
from core.src.world.actions.look import get_look_at_no_target_to_msg
from core.src.world.actions.move import do_move_entity
from core.src.world.actions_scheduler.tools import singleton_action
from core.src.world.builder import follow_system_manager, world_repository
from core.src.world.components.name import NameComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.room import RoomPosition
from core.src.world.entity import Entity
from core.src.world.utils.entity_utils import get_index_from_text, get_entity_data_from_raw_data_input


def get_follow_no_target_to_msg() -> str:
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


def get_follow_target_to_msg(target_alias) -> str:
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


def get_defollow_success() -> str:
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "follow",
            "action": "defollow",
            "status": "success",
        },
        'msg'
    )


def get_follow_movement_msg(followed_alias):
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "follow",
            "action": "move",
            "alias": followed_alias,
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
        entity_data = get_entity_data_from_raw_data_input(target, totals, raw_room_content, index=index)
        if not entity_data:
            await entity.emit_msg(get_look_at_no_target_to_msg())
            return
        if entity_data['entity_id'] == entity.entity_id:
            await _handle_defollow(entity)
            return
        _handle_follow(entity, entity_data)
    except Exception as e:
        LOGGER.core.exception('log exception')
        raise e


async def _handle_defollow(entity):
    await follow_system_manager.stop_following(entity)
    await entity.emit_msg(get_defollow_success())


async def _handle_follow(entity: Entity, followed_data: typing.Dict):
    await follow_system_manager.follow_entity(entity, followed_data['entity_id'])
    alias = followed_data['data'][0]  # Name FIXME TODO - Evaluate data, known, excerpt, etc.
    await entity.emit_msg(get_follow_target_to_msg(alias))


async def do_follow(entity: Entity, movement_event: typing.Dict):
    pos = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)

    followed_name = await world_repository.get_component_value_by_entity_id(
        movement_event['entity']['id'], NameComponent
    )  # FIXME TODO - Evaluate, etc.

    await entity.emit_msg(get_follow_movement_msg(followed_name))
    if pos.value == movement_event['from']:
        await do_move_entity(
            entity,
            PosComponent(movement_event['to']),
            movement_event['direction'],
            reason="movement"
        )
