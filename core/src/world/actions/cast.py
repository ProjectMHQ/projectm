import asyncio

from core.src.auth.logging_factory import LOGGER
from core.src.world.components.pos import PosComponent
from core.src.world.domain.area import Area
from core.src.world.domain.entity import Entity


async def cast_entity(
        entity: Entity,
        where: PosComponent,
        update=True,
        on_connect=False,
        reason=None
):
    from core.src.world.builder import world_repository, events_subscriber_service, events_publisher_service
    loop = asyncio.get_event_loop()
    where.add_previous_position(
        await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
    )
    if update:
        entity = entity.set(where)
        if where.previous_position:
            entity.add_bound(where.previous_position)
        update_response = await world_repository.update_entities(entity.set(where))
        if not update_response:
            LOGGER.core.error(
                'Impossible to cast entity {}, from {} to {}, bounds changed'.format(
                    entity.entity_id, where.previous_position, where
                ))
            return
    if on_connect:
        await events_publisher_service.on_entity_appear_position(entity, where, reason)
    else:
        await events_publisher_service.on_entity_change_position(entity, where, reason)
    loop.create_task(
        events_subscriber_service.subscribe_area(entity, Area(where).make_coordinates())
    )
    return True
