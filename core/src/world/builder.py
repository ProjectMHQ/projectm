import os

import socketio

from core.src.world.actions_scheduler.singleton_actions_scheduler import SingletonActionsScheduler
from core.src.world.messages_translators.builder import get_messages_translator
from core.src.world.repositories.descriptions_repository import RedisDescriptionsRepository
from core.src.world.repositories.library_repository import RedisLibraryRepository
from core.src.world.services.redis_pubsub_interface import PubSubManager
from core.src.world.services.redis_pubsub_publisher_service import RedisPubSubEventsPublisherService
from core.src.world.services.redis_pubsub_subscriber_service import RedisPubSubEventsSubscriberService
from core.src.world.services.transport.socketio_interface import SocketioTransportInterface
from core.src.world.services.transport.websocket_channels_service import WebsocketChannelsService
from core.src.world.services.worker_queue_service import WorkerQueueService
from core.src.world.systems.commands import commands_observer_factory
from core.src.world.systems.connect.manager import ConnectionsManager
from core.src.world.systems.connect.observer import ConnectionsObserver
from core.src.world.services.redis_pubsub_events_observer import PubSubObserver
from core.src.world.systems.follow.manager import FollowSystemManager
from etc import settings

from core.src.auth.repositories.redis_websocket_channels_repository import WebsocketChannelsRepository
from core.src.world.repositories.map_repository import RedisMapRepository
from core.src.world.services.redis_queue import RedisMultipleQueuesPublisher, RedisQueueConsumer
from core.src.world.services.system_utils import get_redis_factory, RedisType
from core.src.auth.builder import strict_redis
from core.src.world.repositories.data_repository import RedisDataRepository

if settings.RUNNING_TESTS and not settings.INTEGRATION_TESTS:
    from unittest.mock import Mock
    async_redis_data = Mock()
    async_redis_queue = Mock()
else:
    async_redis_data = get_redis_factory(RedisType.DATA)
    async_redis_queue = get_redis_factory(RedisType.QUEUES)


WORLD_SYSTEM_PATH = os.getcwd()

library_repository = RedisLibraryRepository(async_redis_data)
map_repository = RedisMapRepository(async_redis_data)
descriptions_repository = RedisDescriptionsRepository(async_redis_data)
world_repository = RedisDataRepository(async_redis_data, library_repository, map_repository)
channels_repository = WebsocketChannelsRepository(strict_redis)
redis_queues_service = RedisMultipleQueuesPublisher(async_redis_queue, num_queues=settings.WORKERS)
websocket_channels_service = WebsocketChannelsService(
    channels_repository=channels_repository,
    data_repository=world_repository,
    redis_queue=redis_queues_service
)

pubsub_manager = PubSubManager(async_redis_queue)
messages_translator = get_messages_translator('it')

events_subscriber_service = RedisPubSubEventsSubscriberService(pubsub_manager)
events_publisher_service = RedisPubSubEventsPublisherService(pubsub_manager)

mgr = socketio.AsyncRedisManager(
    'redis://{}:{}/{}'.format(settings.REDIS_HOST, settings.REDIS_PORT, settings.REDIS_SIO_DB)
)
transport = SocketioTransportInterface(socketio.AsyncServer(client_manager=mgr))

pubsub_observer = PubSubObserver(
    world_repository,
    transport,
    messages_translator
)

async_redis_queues = get_redis_factory(RedisType.QUEUES)
queue = RedisQueueConsumer(async_redis_queues, 0)
worker_queue_manager = WorkerQueueService(queue)
cmds_observer = commands_observer_factory(transport)

connections_manager = ConnectionsManager()
connections_observer = ConnectionsObserver(
    transport,
    pubsub_observer,
    world_repository,
    events_subscriber_service,
    connections_manager
)

singleton_actions_scheduler = SingletonActionsScheduler()

follow_system_manager = FollowSystemManager(
    connections_manager
)
pubsub_observer.add_observer_for_pov_event('follow', follow_system_manager)
