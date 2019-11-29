import asyncio

import socketio

from core.src.auth.logging_factory import LOGGER
from core.src.world.actions_scheduler.singleton_actions_scheduler import SingletonActionsScheduler
from core.src.world.builder import pubsub, events_subscriber_service, channels_repository, messages_translator, \
    world_repository, pubsub_observer
from core.src.world.components.pos import PosComponent
from core.src.world.services.redis_queue import RedisQueueConsumer
from core.src.world.services.transport.socketio_interface import SocketioTransportInterface
from core.src.world.services.system_utils import RedisType, get_redis_factory
from core.src.world.services.worker_queue_service import WorkerQueueService
from core.src.world.systems.commands import commands_observer_factory
from core.src.world.systems.connect.observer import ConnectionsObserver

from etc import settings

loop = asyncio.get_event_loop()
async_redis_queues = get_redis_factory(RedisType.QUEUES)
queue = RedisQueueConsumer(async_redis_queues, 0)
worker_queue_manager = WorkerQueueService(loop, queue)
mgr = socketio.AsyncRedisManager(
    'redis://{}:{}'.format(settings.REDIS_HOST, settings.REDIS_PORT)
)
transport = SocketioTransportInterface(
    socketio.AsyncServer(client_manager=mgr),
    messages_translator_strategy=messages_translator
)

cmds_observer = commands_observer_factory(transport)
connections_observer = ConnectionsObserver(transport)
singleton_actions_scheduler = SingletonActionsScheduler()

worker_queue_manager.add_queue_observer('connected', connections_observer)
worker_queue_manager.add_queue_observer('disconnected', connections_observer)
worker_queue_manager.add_queue_observer('cmd', cmds_observer)


async def main(entity_ids):
    data = world_repository.get_components_values_by_components(
        entity_ids, [PosComponent]
    )[PosComponent.component_enum]
    await events_subscriber_service.bootstrap_subscribes(data)
    for entity_id in entity_ids:
        events_subscriber_service.add_observer_for_entity_id(entity_id, pubsub_observer)
    await worker_queue_manager.run()


def check_entities_connection_status():
    from core.src.world.builder import world_repository
    from core.src.world.components.connection import ConnectionComponent
    from core.src.world.entity import Entity

    connected_entity_ids = [x for x in world_repository.get_entity_ids_with_components(ConnectionComponent)]
    if not connected_entity_ids:
        return
    # FIXME TODO multiprocess workers must discriminate and works only on their own entities

    components_values = world_repository.get_raw_component_value_by_entity_ids(
        ConnectionComponent, *connected_entity_ids
    )

    channels = channels_repository.get_many(*components_values)
    to_update = []
    online = []
    for i, ch in enumerate(channels.values()):
        if not ch:
            to_update.append(Entity(connected_entity_ids[i]).set(ConnectionComponent("")))
        else:
            online.append(connected_entity_ids[i])
    world_repository.update_entities(*to_update)
    return online


if __name__ == '__main__':
    LOGGER.core.debug('Starting Worker')
    online_entities = check_entities_connection_status()
    loop.create_task(pubsub.start())
    loop.run_until_complete(main(online_entities))
