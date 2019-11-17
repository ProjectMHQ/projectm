from core.src.world.builder import map_repository, world_repository
from core.src.world.components.pos import PosComponent
from core.src.world.domain.area import Area
from core.src.world.domain.room import RoomPosition
from core.src.world.entity import Entity


async def getmap(entity: Entity):
    pos = world_repository.get_component_value_by_entity(entity.entity_id, PosComponent)
    base_area = await Area(pos).get_rooms()
    await entity.emit_msg(
        {
            "event": "getmap",
            "base": base_area,
            "data": []
        },
        topic="map"
    )
