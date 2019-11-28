import asyncio

import socketio

from core.src.auth.logging_factory import LOGGER
from core.src.world.actions_scheduler.singleton_actions_scheduler import SingletonActionsScheduler
from core.src.world.builder import pubsub
from core.src.world.services.redis_queue import RedisQueueConsumer
from core.src.world.services.websocket.socketio_interface import SocketioTransportInterface
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
transport = SocketioTransportInterface(socketio.AsyncServer(client_manager=mgr))
cmds_observer = commands_observer_factory(transport)
connections_observer = ConnectionsObserver(transport)

singleton_actions_scheduler = SingletonActionsScheduler()

worker_queue_manager.add_queue_observer('connected', connections_observer)
worker_queue_manager.add_queue_observer('cmd', cmds_observer)

if __name__ == '__main__':
    LOGGER.core.debug('Starting Worker')
    print('Starting Worker')
    loop.create_task(pubsub.start())
    loop.run_until_complete(worker_queue_manager.run())
