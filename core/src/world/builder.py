from core.src.world.repositories.descriptions_repository import RedisDescriptionsRepository
from core.src.world.services.redis_pubsub_interface import PubSub
from core.src.world.services.redis_pubsub_publisher_service import RedisPubSubEventsPublisherService
from core.src.world.services.redis_pubsub_subscriber_service import RedisPubSubEventsSubscriberService
from core.src.world.services.websocket.websocket_channels_service import WebsocketChannelsService
from etc import settings

from core.src.auth.repositories.redis_websocket_channels_repository import WebsocketChannelsRepository
from core.src.world.repositories.map_repository import RedisMapRepository
from core.src.world.services.redis_queue import RedisMultipleQueuesPublisher
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


map_repository = RedisMapRepository(async_redis_data)
descriptions_repository = RedisDescriptionsRepository(async_redis_data)
world_repository = RedisDataRepository(strict_redis)
channels_repository = WebsocketChannelsRepository(strict_redis)
redis_queues_service = RedisMultipleQueuesPublisher(async_redis_queue, num_queues=settings.WORKERS)
websocket_channels_service = WebsocketChannelsService(
    channels_repository=channels_repository,
    data_repository=world_repository,
    redis_queue=redis_queues_service
)
pubsub = PubSub(async_redis_data)
events_subscriber_service = RedisPubSubEventsSubscriberService(pubsub)
events_publisher_service = RedisPubSubEventsPublisherService(pubsub)
