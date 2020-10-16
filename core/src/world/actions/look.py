import typing
import itertools
from core.src.auth.logging_factory import LOGGER
from core.src.world.actions.utils.utils import DirectionEnum, direction_to_coords_delta, apply_delta_to_position
from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.room import RoomPosition
from core.src.world.domain.entity import Entity
from core.src.world.utils.entity_utils import get_entity_id_from_raw_data_input, get_index_from_text


def get_look_at_direction_to_msg(d: DirectionEnum):
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "look",
            "target": "direction",
            "status": "success",
            "value": d
        },
        'msg'
    )


def get_look_at_no_direction_to_msg(d: str):
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "look",
            "target": "direction",
            "status": "failure",
            "reason": "value_error",
            "value": d
        },
        'msg'
    )


def get_look_at_no_target_to_msg():
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "look",
            "target": "entity",
            "status": "failure",
            "reason": "not_found"
        },
        'msg'
    )


def get_look_at_target_to_msg(response: typing.Dict, is_self=False):
    from core.src.world.builder import messages_translator
    if response['known']:
        target_alias = response['name']
    else:
        target_alias = response['excerpt']
    return messages_translator.payload_msg_to_string(
        {
            "event": "look",
            "target": "entity",
            "status": "success",
            "alias": target_alias,
            "is_self": is_self
        },
        'msg'
    )


async def look(entity: Entity, *targets):
    from core.src.world.builder import map_repository, world_repository
    if not targets:
        pos = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
        room = await map_repository.get_room(RoomPosition(x=pos.x, y=pos.y, z=pos.z))
        await room.populate_room_content_for_look(entity)
        await entity.emit_system_event(
            {
                "event": "look",
                "target": "room",
                "details": {
                    "title": room.title,
                    "description": room.description,
                    "content": room.json_content,
                    "pos": [room.position.x, room.position.y, room.position.z]
                }
            }
        )
    elif len(targets) == 1 and targets[0] in (x.value for x in DirectionEnum):
        await _handle_direction_look(entity, targets)
    elif len(targets) <= 2:
        await _handle_targeted_look(entity, *targets)


async def _handle_direction_look(entity, targets):
    if targets[0] in ('u', 'd'):
        """
        evaluate sight
        """
        return  # FIXME - TODO

    from core.src.world.builder import map_repository, world_repository
    try:
        direction_enum = DirectionEnum(targets[0])
        delta = direction_to_coords_delta(direction_enum)
    except ValueError:
        direction_enum = delta = None
    if delta:
        pos = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
        look_cords = apply_delta_to_position(pos, delta)
        room = await map_repository.get_room(RoomPosition(x=look_cords.x, y=look_cords.y, z=look_cords.z))
        await room.populate_room_content_for_look(entity)
        await entity.emit_msg(get_look_at_direction_to_msg(direction_enum))
        await entity.emit_system_event(
            {
                "event": "look",
                "target": "direction",
                "details": {
                    "title": room.title,
                    "description": room.description,
                    "content": room.json_content,
                    "pos": [room.position.x, room.position.y, room.position.z]
                }
            }
        )
        return
    else:
        await entity.emit_msg(get_look_at_no_direction_to_msg(targets[0]))


async def _handle_targeted_look(entity, *targets):
    if len(targets) > 1:
        await entity.emit_msg('Command error - Multi targets not implemented yet')
        return
    from core.src.world.builder import world_repository, map_repository
    data = await world_repository.get_components_values_by_entities(
        [entity],
        [PosComponent, AttributesComponent]
    )
    pos = PosComponent(data[entity.entity_id][PosComponent.component_enum])
    attrs_value = data[entity.entity_id][AttributesComponent.component_enum]
    room = await map_repository.get_room(RoomPosition(x=pos.x, y=pos.y, z=pos.z))
    if not room.has_entities:
        await entity.emit_msg(get_look_at_no_target_to_msg())
        return
    try:
        await room.populate_room_content_for_look(entity)
        totals, raw_room_content = await world_repository.get_raw_content_for_room_interaction(entity.entity_id, room)
        personal_data = [
            {
                'entity_id': entity.entity_id, 'data': [attrs_value, *('' for _ in range(1, totals))]
            },
            {
                'entity_id': entity.entity_id, 'data': [{'keyword': attrs_value['name']}]
            },
        ]

        raw_room_content = itertools.chain(raw_room_content, personal_data)
        index, target = get_index_from_text(targets[0])
        found_entity = get_entity_id_from_raw_data_input(target, totals, raw_room_content, index=index)
        if not found_entity or not found_entity[0]:
            await entity.emit_msg(get_look_at_no_target_to_msg())
            return
        else:
            entity_id, entity_keyword = found_entity

        response = await world_repository.get_look_components_for_entity_id(entity_id)
        is_self = True
        if entity.entity_id != entity_id:
            is_self = False
            if response['type'] == 0:
                from core.src.world.builder import events_publisher_service
                action = {'action': 'look'}
                await events_publisher_service.on_entity_do_public_action(entity, pos, action, entity_id)

        await entity.emit_msg(get_look_at_target_to_msg(response, is_self=is_self))
        await entity.emit_system_event(
            {
                "event": "look",
                "target": "entity",
                "details": {
                    "title": response['name'],
                    "known": response['known'],
                    "description": response['description'],
                    "type": response['type'],
                    "status": response['status']
                }
            }
        )
    except Exception as e:
        LOGGER.core.exception('log exception')
        raise e
