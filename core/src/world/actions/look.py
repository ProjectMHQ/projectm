from core.src.world.builder import map_repository, world_repository
from core.src.world.components.pos import PosComponent
from core.src.world.domain.room import RoomPosition
from core.src.world.entity import Entity


async def look(entity: Entity, *targets):
    if targets:
        await entity.emit_msg(
            {
                "event": "look",
                "error": "Command not implemented"
            }
        )
    else:
        pos = world_repository.get_component_value_by_entity(entity.entity_id, PosComponent)
        if not pos:
            await entity.emit_msg(
                {
                    "event": "look",
                    "title": "Nowhere",
                    "description": "A non place",
                    "content": []
                }
            )
        else:
            room = await map_repository.get_room(RoomPosition(x=pos.x, y=pos.y, z=pos.z))
            await entity.emit_msg(
                {
                    "event": "look",
                    "title": room.title,
                    "description": room.description,
                    "content": room.content
                }
            )
