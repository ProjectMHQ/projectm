import asyncio

from core.src.world.actions import singleton_action
from core.src.world.builder import world_repository, events_subscriber_service, events_publisher_service
from core.src.world.components.pos import PosComponent
from core.src.world.domain.area import Area
from core.src.world.entity import Entity


@singleton_action
async def cast_entity(entity: Entity, where: PosComponent, update=True):
    loop = asyncio.get_event_loop()
    update and world_repository.update_entities(entity.set(where))
    loop.create_task(events_publisher_service.on_entity_join_room(entity, where))
    loop.create_task(events_subscriber_service.subscribe_area(entity, Area(where).make_coordinates()))

