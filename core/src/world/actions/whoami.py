import json

from core.src.world.components.attributes import AttributesComponent
from core.src.world.domain.entity import Entity


async def whoami(entity: Entity):
    from core.src.world.builder import world_repository
    attributes = await world_repository.get_component_value_by_entity_id(entity.entity_id, AttributesComponent)
    await entity.emit_msg(
        json.dumps(
            {
                "event": "whoami",
                "id": entity.entity_id,
                "name": attributes.name
            }
        )

    )
