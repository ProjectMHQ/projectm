from core.src.world.builder import events_subscriber_service, channels_repository, \
    world_repository, pubsub_observer, worker_queue_manager, cmds_observer, connections_observer, pubsub_manager, \
    transport, connections_manager, library_repository
from core.src.world.components.pos import PosComponent
from core.src.world.components.connection import ConnectionComponent
from core.src.world.domain.entity import Entity
from core.src.world.utils.world_types import Transport

worker_queue_manager.add_queue_observer('connected', connections_observer)
worker_queue_manager.add_queue_observer('disconnected', connections_observer)
worker_queue_manager.add_queue_observer('cmd', cmds_observer)


async def main(entities):
    await library_repository.build()
    if entities:
        data = (await world_repository.get_components_values_by_components(
            [x['entity_id'] for x in entities], [PosComponent]
        ))[PosComponent.component_enum]
        await events_subscriber_service.bootstrap_subscribes(data)
        for entity_data in entities:
            events_subscriber_service.add_observer_for_entity_data(entity_data, pubsub_observer)
    await worker_queue_manager.run()


async def check_entities_connection_status():
    connected_entity_ids = [x for x in (await world_repository.get_entity_ids_with_components(ConnectionComponent))]
    if not connected_entity_ids:
        return []
    # FIXME TODO multiprocess workers must discriminate and works only on their own entities

    components_values = list(
        await world_repository.get_raw_component_value_by_entity_ids(
            ConnectionComponent, *connected_entity_ids
        )
    )
    to_update = []
    online = []
    if components_values:
        channels = channels_repository.get_many(*components_values)
        for i, ch in enumerate(channels.values()):
            if not ch:
                to_update.append(Entity(connected_entity_ids[i]).set_for_update(ConnectionComponent("")))
            else:
                _transport_item = Transport(ch.id, transport)
                online.append(
                    {
                        'entity_id': connected_entity_ids[i],
                        'transport': _transport_item
                    }
                )
                connections_manager.set_transport(connected_entity_ids[i], _transport_item)
    await world_repository.update_entities(*to_update)
    return online


if __name__ == '__main__':
    from core.src.auth.logging_factory import LOGGER
    import asyncio

    loop = asyncio.get_event_loop()
    LOGGER.core.debug('Starting Worker')
    online_entities = loop.run_until_complete(check_entities_connection_status())
    loop.create_task(pubsub_manager.start())
    loop.run_until_complete(main(online_entities))
