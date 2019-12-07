from core.src.world.entity import Entity


async def whoami(entity: Entity):
    await entity.emit_system_event(
        {
            "event": "whoami",
            "id": entity.entity_id
        }
    )
