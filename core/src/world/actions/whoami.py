from core.src.world.entity import Entity


async def whoami(entity: Entity):
    await entity.emit_msg(
        {
            "event": "whoami",
            "id": entity.entity_id
        }
    )
