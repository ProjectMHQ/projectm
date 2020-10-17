import itertools

import typing

from core.src.auth.logging_factory import LOGGER
from core.src.world.actions.movement._utils_ import DirectionEnum
from core.src.world.actions.movement.move import do_move_entity
from core.src.world.actions_scheduler.tools import singleton_action
from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.entity import Entity
from core.src.world.utils.entity_utils import get_index_from_text, get_entity_data_from_raw_data_input


def get_follow_failure_to_msg(reason) -> str:
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "follow",
            "action": "follow",
            "target": "entity",
            "status": "failure",
            "reason": reason
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


def get_unfollow_success() -> str:
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "follow",
            "action": "unfollow",
            "status": "success",
        },
        'msg'
    )


def get_follow_movement_msg(followed_alias, direction):
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "follow",
            "action": "move",
            "alias": followed_alias,
            "direction": direction
        },
        'msg'
    )


@singleton_action
async def follow(
    entity: Entity,
    *target: str
):
    from core.src.world.builder import world_repository, map_repository
    data = await world_repository.get_components_values_by_entities(
        [entity],
        [PosComponent, AttributesComponent]
    )
    pos = PosComponent(data[entity.entity_id][PosComponent.component_enum])
    attributes_value = data[entity.entity_id][AttributesComponent.component_enum]
    room = await map_repository.get_room(pos)

    if not len(target):
        return await _handle_defollow(entity, pos)
    elif len(target) > 1:
        return
    else:
        target = target[0]

    if not room.has_entities:
        await entity.emit_msg(get_follow_failure_to_msg('not_found'))
        return
    try:
        await room.populate_room_content_for_look(entity)
        totals, raw_room_content = await world_repository.get_raw_content_for_room_interaction(entity.entity_id, room)
        raw_room_content = itertools.chain(
            raw_room_content,
            (x for x in [
                {'entity_id': entity.entity_id, 'data': [attributes_value, *('' for _ in range(1, totals))]}]
             )
        )
        index, target = get_index_from_text(target)
        entity_data = get_entity_data_from_raw_data_input(target, totals, raw_room_content, index=index)
        if not entity_data:
            await entity.emit_msg('Non lo vedi qui')  # todo fixme
            return
        if entity.entity_id == entity_data['entity_id']:
            await _handle_defollow(entity, pos)
            return
        await _handle_follow(entity, entity_data, pos)
    except Exception as e:
        LOGGER.core.exception('log exception')
        raise e


async def _handle_defollow(entity, room):
    from core.src.world.builder import follow_system_manager, events_publisher_service
    followed = follow_system_manager.stop_following(entity.entity_id)
    await entity.emit_msg(get_unfollow_success())
    payload = {"action": "unfollow"}
    await events_publisher_service.on_entity_do_public_action(
        entity, room, payload, followed
    )


async def _handle_follow(entity: Entity, followed_data: typing.Dict, room):
    from core.src.world.builder import follow_system_manager, events_publisher_service
    if follow_system_manager.is_follow_repetition(entity.entity_id, followed_data['entity_id']):
        return await entity.emit_msg(get_follow_failure_to_msg('repeat'))
    if follow_system_manager.is_follow_loop(entity.entity_id, followed_data['entity_id']):
        return await entity.emit_msg(get_follow_failure_to_msg('loop'))
    follow_system_manager.follow_entity(entity.entity_id, followed_data['entity_id'])
    alias = followed_data['data'][0]['keyword']
    await entity.emit_msg(get_follow_target_to_msg(alias))
    payload = {"action": "follow"}
    await events_publisher_service.on_entity_do_public_action(
        entity, room, payload, followed_data['entity_id']
    )


async def do_follow(entity: Entity, movement_event: typing.Dict):
    from core.src.world.builder import world_repository
    pos = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)

    followed_name = await world_repository.get_component_value_by_entity_id(
        movement_event['entity']['id'], AttributesComponent
    )  # FIXME TODO - Evaluate, etc.

    await entity.emit_msg(get_follow_movement_msg(followed_name.name, movement_event['direction']))
    if pos.value == movement_event['from']:
        await do_move_entity(
            entity,
            PosComponent(movement_event['to']),
            DirectionEnum(movement_event['direction']),
            reason="movement",
            emit_msg=False
        )
