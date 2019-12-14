from core.src.world.actions.utils.utils import DirectionEnum, direction_to_coords_delta, apply_delta_to_position
from core.src.world.components.name import NameComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.room import RoomPosition
from core.src.world.entity import Entity
from core.src.world.utils.entity_utils import get_entity_id_from_raw_data_input


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


def get_look_at_no_direction_to_msg(d: DirectionEnum):
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


def get_look_at_target_to_msg(target_alias: str):
    from core.src.world.builder import messages_translator
    return messages_translator.payload_msg_to_string(
        {
            "event": "look",
            "target": "entity",
            "status": "success",
            "what": target_alias
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
                "title": room.title,
                "description": room.description,
                "content": room.json_content,
                "pos": [room.position.x, room.position.y, room.position.z]
            }
        )
        return
    if len(targets) == 1 and len(targets[0]) == 1:
        return await _handle_direction_look(entity, targets)
    elif len(targets) <= 2 and len(targets[0]) >= 3:
        return await _handle_targeted_look(entity, *targets)
    await entity.emit_system_event(
        {
            "event": "look",
            "error": "Command error"
        }
    )


async def _handle_direction_look(entity, targets):
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
                "target": "room",
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
        await entity.emit_msg(get_look_at_no_direction_to_msg(direction_enum))


async def _handle_targeted_look(entity, *targets):
    if len(*targets) > 1:
        await entity.emit_system_event(
            {
                "event": "look",
                "error": "Command error - Multi targets not implemented yet"
            }
        )
    from core.src.world.builder import world_repository, map_repository
    pos = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
    room = await map_repository.get_room(RoomPosition(x=pos.x, y=pos.y, z=pos.z))
    if not room.has_content:
        await entity.emit_msg(get_look_at_no_target_to_msg())
        return

    totals, raw_room_content = await world_repository.get_raw_content_for_room_interaction(entity.entity_id, room)
    entity_id = get_entity_id_from_raw_data_input(targets[0], totals, raw_room_content)
    if not entity_id:
        await entity.emit_msg(get_look_at_no_target_to_msg())
        return

    response = await world_repository.get_look_components_for_entity_id(entity_id)
    await entity.emit_msg(get_look_at_target_to_msg(response))
    await entity.emit_system_event(
        {
            "event": "look",
            "target": "entity",
            "details": {
                "title": response[NameComponent],
                "known": True,
                "description": "<character full description placeholder>",
                "type": 0,
                "status": 0
            }
        }
    )

    if not entity_id:
        await entity.emit_system_event(
            {
                "event": "look",
                "error": "'{}' is not here".format(targets[0])
            }
        )
