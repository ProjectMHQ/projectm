import asyncio

from core.src.world.actions import singleton_action
from core.src.world.builder import world_repository, events_subscriber_service, events_publisher_service
from core.src.world.components.connection import ConnectionComponent
from core.src.world.components.pos import PosComponent
from core.src.world.entity import Entity


@singleton_action
async def disconnect_entity(entity: Entity, where: PosComponent, update=True):
    loop = asyncio.get_event_loop()
    entity.set(ConnectionComponent(""))
    update and world_repository.update_entities()
    await events_subscriber_service.unsubscribe_all(entity)
    loop.create_task(events_publisher_service.on_entity_disappear_from_room(entity, where))



