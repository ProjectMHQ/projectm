import json

from core.src.world.components.attributes import AttributesComponent
from core.src.world.domain.entity import Entity
from core.src.world.utils.entity_utils import load_components


async def whoami(entity: Entity):
    await load_components(entity, AttributesComponent)
    await entity.emit_msg(
        json.dumps(
            {
                "event": "whoami",
                "id": entity.entity_id,
                "name": entity.get_component(AttributesComponent).name
            }
        )
    )
