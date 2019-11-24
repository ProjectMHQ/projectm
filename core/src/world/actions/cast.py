from core.src.world.actions import singleton_scheduled_action
from core.src.world.builder import world_repository
from core.src.world.components.pos import PosComponent
from core.src.world.entity import Entity


@singleton_scheduled_action
async def cast_entity(entity: Entity, where: PosComponent):
    world_repository.update_entities(entity.set(where))


