from core.src.world.builder import map_repository, world_repository
from core.src.world.components.pos import PosComponent
from core.src.world.domain.room import RoomPosition


async def look(
    entity_id: int,
    *targets,
    callback=None,
    errback=None
):
    if targets:
        errback("Command Not Implemented")
    else:
        pos = world_repository.get_component_value_by_entity(entity_id, PosComponent)
        room = await map_repository.get_room(RoomPosition(x=pos.x, y=pos.y, z=pos.z))
        await callback(
            {
                {
                        "title": room.title,
                        "description": room.description,
                        "content": room.content
                }
            }
        )
