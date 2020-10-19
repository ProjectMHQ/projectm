import time

from core.src.auth.logging_factory import LOGGER
from core.src.world.components.pos import PosComponent
from core.src.world.domain.area import Area
from core.src.world.domain.entity import Entity
from core.src.world.utils.messaging import emit_sys_msg


async def getmap(entity: Entity):
    start = time.time()
    from core.src.world.builder import world_repository
    pos = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
    assert pos
    area = Area(pos)
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
    LOGGER.websocket_monitor.debug('Map served in %s', '{:.4f}'.format(time.time() - start))
