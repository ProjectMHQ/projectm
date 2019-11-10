from core.src.world.services.websocket_channels_service import WebsocketChannelsService
from etc import settings

from core.src.auth.repositories.redis_websocket_channels_repository import WebsocketChannelsRepository
from core.src.world.repositories.map_repository import RedisMapRepository
from core.src.world.services.redis_queue import RedisMultipleQueuesPublisher
from core.src.world.utils import async_redis_pool_factory
from core.src.auth.builder import strict_redis
from core.src.world.repositories.data_repository import RedisDataRepository


map_repository = RedisMapRepository(async_redis_pool_factory)
world_repository = RedisDataRepository(strict_redis)
channels_repository = WebsocketChannelsRepository(strict_redis)
redis_queues_service = RedisMultipleQueuesPublisher(
    async_redis_pool_factory,
    num_queues=settings.WORKERS
)
websocket_channels_service = WebsocketChannelsService(
    channels_repository=channels_repository,
    data_repository=world_repository,
    redis_queue=redis_queues_service
)
