import asyncio

import socketio

from core.src.auth.logging_factory import LOGGER
from core.src.world.services.redis_queue import RedisQueueConsumer
from core.src.world.services.socketio_interface import SocketioTransportInterface
from core.src.world.services.worker_queue_service import WorkerQueueService
from core.src.world.systems.commands import commands_observer_factory
from core.src.world.services.system_utils import async_redis_pool_factory
from core.src.world.systems.connect.observer import ConnectionsObserver

from etc import settings

loop = asyncio.get_event_loop()
queue = RedisQueueConsumer(async_redis_pool_factory, 0)
worker_queue_manager = WorkerQueueService(loop, queue)
transport = SocketioTransportInterface(
    socketio.AsyncRedisManager(
        'redis://{}:{}'.format(settings.REDIS_HOST, settings.REDIS_PORT)
    )
)
cmds_observer = commands_observer_factory(transport)
connections_observer = ConnectionsObserver(transport)

worker_queue_manager.add_queue_observer('connected', connections_observer)
worker_queue_manager.add_queue_observer('cmd', cmds_observer)


if __name__ == '__main__':
    LOGGER.core.debug('Starting Worker')
    print('Starting Worker')
    loop.run_until_complete(worker_queue_manager.run())
