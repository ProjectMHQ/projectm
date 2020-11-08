import asyncio

from core.src.auth.logging_factory import LOGGER
from core.src.world.components.position import PositionComponent
from core.src.world.domain.area import Area
from core.src.world.domain.entity import Entity
from core.src.world.domain.room import Room
from core.src.world.utils.messaging import get_eligible_listeners_for_area


async def cast_entity(
        entity: Entity,
        position: PositionComponent,
        update=True,
        on_connect=False,
        reason=None
):
    assert isinstance(position, PositionComponent)
    from core.src.world.builder import world_repository, events_subscriber_service, events_publisher_service
    loop = asyncio.get_event_loop()
    if update:
        entity = entity.set_for_update(position).set_room(Room(position))
        update_response = await world_repository.update_entities(entity.set_for_update(position))
        if not update_response:
            LOGGER.core.error(
                'Impossible to cast entity {}'.format(entity.entity_id))
            return
    area = Area(position).make_coordinates()
    listeners = await get_eligible_listeners_for_area(area)
    entity.entity_id in listeners and listeners.remove(entity.entity_id)
    if on_connect:
        await events_publisher_service.on_entity_appear_position(entity, position, reason, targets=listeners)
        loop.create_task(events_subscriber_service.subscribe_events(entity))
    else:
        pass
        await events_publisher_service.on_entity_change_position(entity, position, reason, targets=listeners)
    entity.set_component(position)
    return True
