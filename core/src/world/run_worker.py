import asyncio

import socketio

from core.src.auth.logging_factory import LOGGER
from core.src.world.services.redis_queue import RedisQueueConsumer
from core.src.world.services.worker_queue_service import WorkerQueueService
from core.src.world.systems.commands import commands_observer_factory
from core.src.world.utils import async_redis_pool_factory

from etc import settings

loop = asyncio.get_event_loop()
queue = RedisQueueConsumer(async_redis_pool_factory, 0)
worker_queue_manager = WorkerQueueService(loop, queue)
transport = socketio.AsyncRedisManager(
    'redis://{}:{}'.format(settings.REDIS_HOST, settings.REDIS_PORT)
)
cmds_observer = commands_observer_factory(transport)
worker_queue_manager.add_messages_observer('cmd', cmds_observer)


if __name__ == '__main__':
    LOGGER.core.debug('Starting Worker')
    print('Starting Worker')
    loop.run_until_complete(worker_queue_manager.run())
