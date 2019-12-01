from core.src.world.components.pos import PosComponent
from core.src.world.domain.room import RoomPosition
from core.src.world.entity import Entity


async def whoami(entity: Entity):
    await entity.emit_msg(
        {
            "event": "whoami",
            "id": entity.entity_id,
        }
    )
