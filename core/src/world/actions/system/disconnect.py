from core.src.world.actions_scheduler.tools import singleton_action
from core.src.world.components.connection import ConnectionComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.area import Area
from core.src.world.domain.entity import Entity


@singleton_action
async def disconnect_entity(entity: Entity):
    from core.src.world.builder import world_repository, events_publisher_service, map_repository
    entity.set(ConnectionComponent(""))
    await world_repository.update_entities(entity)
    where = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
    area = Area(where).make_coordinates()
    listeners = await world_repository.get_elegible_listeners_for_area(area)
    await map_repository.remove_entity_from_map(entity.entity_id, where)
    await events_publisher_service.on_entity_disappear_position(entity, where, "disconnect", listeners)
    await entity.emit_system_event({"event": "disconnect", "reason": "quit"})
    await events_publisher_service.on_entity_quit_world(entity)
