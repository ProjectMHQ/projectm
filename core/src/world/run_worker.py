from core.src.world.builder import events_subscriber_service, library_repository, \
    pubsub_observer, worker_queue_manager, cmds_observer, connections_observer, pubsub_manager
from core.src.world.utils.entity_utils import check_entities_connection_status
from core.src.world.utils.world_utils import clean_rooms_from_stales_instances

worker_queue_manager.add_queue_observer('connected', connections_observer)
worker_queue_manager.add_queue_observer('disconnected', connections_observer)
worker_queue_manager.add_queue_observer('cmd', cmds_observer)


async def main(entities):
    await library_repository.build()
    if entities:
        await events_subscriber_service.bootstrap_subscribes(entities)
        for entity_data in entities:
            events_subscriber_service.add_observer_for_entity_data(entity_data, pubsub_observer)
    await worker_queue_manager.run()


if __name__ == '__main__':
    from core.src.auth.logging_factory import LOGGER
    import asyncio

    loop = asyncio.get_event_loop()
    LOGGER.core.debug('Starting Worker')
    loop.run_until_complete(clean_rooms_from_stales_instances())
    online_entities = loop.run_until_complete(check_entities_connection_status())
    loop.create_task(pubsub_manager.start())
    loop.run_until_complete(main(online_entities))
