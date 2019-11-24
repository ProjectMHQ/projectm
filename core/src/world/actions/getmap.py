from core.src.world.builder import world_repository
from core.src.world.components.pos import PosComponent
from core.src.world.domain.area import Area
from core.src.world.entity import Entity


async def getmap(entity: Entity):
    pos = world_repository.get_component_value_by_entity(entity.entity_id, PosComponent)
    assert pos
    area_map = await Area(pos).get_map()
    await entity.emit_msg(
        {
            "event": "map",
            "base": area_map["base"],
            "data": area_map["data"]
        },
        topic="map"
    )
