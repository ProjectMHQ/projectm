from core.src.world.actions.utils.utils import DirectionEnum, direction_to_coords_delta, apply_delta_to_position
from core.src.world.components.pos import PosComponent
from core.src.world.domain.room import RoomPosition
from core.src.world.entity import Entity


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
        pos = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
        return await _handle_direction_look(entity, pos, targets)
    await entity.emit_system_event(
        {
            "event": "look",
            "error": "Command error"
        }
    )


async def _handle_direction_look(entity, pos, targets):
    from core.src.world.builder import map_repository
    try:
        delta = direction_to_coords_delta(DirectionEnum(targets[0]))
    except ValueError:
        delta = None
    if delta:
        look_cords = apply_delta_to_position(pos, delta)
        room = await map_repository.get_room(RoomPosition(x=look_cords.x, y=look_cords.y, z=look_cords.z))
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
    else:
        await entity.emit_system_event(
            {
                "event": "look",
                "error": "Command error: '{}' is not a direction".format(targets[0])
            }
        )
