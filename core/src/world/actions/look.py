from core.src.world.components.pos import PosComponent
from core.src.world.domain.room import RoomPosition
from core.src.world.entity import Entity


async def look(entity: Entity, *targets):
    from core.src.world.builder import map_repository, world_repository
    if targets:
        await entity.emit_system_event(
            {
                "event": "look",
                "error": "Command not implemented"
            }
        )
    else:
        pos = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
        room = await map_repository.get_room(RoomPosition(x=pos.x, y=pos.y, z=pos.z))
        await entity.emit_system_event(
            {
                "event": "look",
                "title": room.title,
                "description": room.description,
                "content": room.content,
                "pos": [room.position.x, room.position.y, room.position.z]
            }
        )
