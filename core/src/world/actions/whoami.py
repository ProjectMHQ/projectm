import json

from core.src.world.components.name import NameComponent
from core.src.world.entity import Entity


async def whoami(entity: Entity):
    from core.src.world.builder import world_repository
    name = await world_repository.get_component_value_by_entity_id(entity.entity_id, NameComponent)
    await entity.emit_msg(
        json.dumps(
            {
                "event": "whoami",
                "id": entity.entity_id,
                "name": name.value
            }
        )

    )
