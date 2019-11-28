from core.src.world.actions import singleton_scheduled_action
from core.src.world.builder import world_repository, events_publisher_service
from core.src.world.components.pos import PosComponent
from core.src.world.entity import Entity


@singleton_scheduled_action
async def cast_entity(entity: Entity, where: PosComponent):
    current_position = world_repository.get_component_value_by_entity(entity.entity_id, PosComponent)
    await events_publisher_service.on_entity_left_room(entity, current_position)
    world_repository.update_entities(entity.set(where))
    await events_publisher_service.on_entity_join_room(entity, where)
