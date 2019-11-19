from core.src.world.builder import world_repository
from core.src.world.components.pos import PosComponent
from core.src.world.entity import Entity


async def cast_entity(entity: Entity, where: PosComponent):
    world_repository.update_entities(entity.set(where))

