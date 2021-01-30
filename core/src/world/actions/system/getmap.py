from core.src.world.domain.area import Area
from core.src.world.domain.entity import Entity
from core.src.world.utils.messaging import emit_sys_msg
from core.src.world.utils.world_utils import get_current_room


async def getmap(entity: Entity):
    room = await get_current_room(entity, populate=False)
    area = Area(room.position)
    area_map = await area.get_map_for_entity(entity)
    await emit_sys_msg(
        entity,
        "map",
        {
            "event": "map",
            "base": area_map["base"],
            "data": area_map["data"],
            "shape": [area.size, area.size]  # placeholder for rows, cols
        }
    )
