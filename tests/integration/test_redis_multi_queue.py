from etc import settings
import asyncio
from unittest import TestCase
from core.src.auth.builder import strict_redis
from core.src.world.services.redis_queue import RedisMultipleQueuesPublisher, RedisQueueConsumer
from core.src.world.services.worker_queue_service import WorkerQueueService
from core.src.world.utils import async_redis_pool_factory


class TestRedisMultiQueue(TestCase):
    def setUp(self):
        strict_redis.flushdb(settings.REDIS_TEST_DB)
        self.loop = asyncio.get_event_loop()
        self.publisher = RedisMultipleQueuesPublisher(
            async_redis_pool_factory,
            num_queues=5
        )
        self.consumers = [
            RedisQueueConsumer(async_redis_pool_factory, x) for x in range(0, 5)
        ]

    async def async_test(self):
        ids = dict(
            prova3asdfaaa1=0,
            prova3=1,
            prova2=2,
            prova=3,
            prova3asdfaa=4
        )
        for cid, cidv in ids.items():
            await self.publisher.put({'message': cid})
            self.assertEqual(await self.consumers[cidv].get(), {'message': cid, 'e_id': cid})

    def test(self):
        self.loop.run_until_complete(self.async_test())


class TestRedisWorkerQueueService(TestCase):
    def setUp(self):
        self.messages = []
        strict_redis.flushdb(settings.REDIS_TEST_DB)
        self.loop = asyncio.get_event_loop()
        self.publisher = RedisMultipleQueuesPublisher(
            async_redis_pool_factory,
            num_queues=5
        )
        self.workers = [
            WorkerQueueService(
                self.loop,
                RedisQueueConsumer(async_redis_pool_factory, x)
            ) for x in range(0, 5)
        ]

        class Obs:
            @staticmethod
            async def on_message(msg):
                self.messages.append(msg)

        self.observers = []
        for i, worker in enumerate(self.workers):
            self.loop.create_task(worker.run())
            self.observers.append(Obs())
            worker.add_messages_observer('cmd', self.observers[i])

    async def on_message(self, message):
        self.messages.append(message)

    async def dummy(self):
        return

    async def async_test(self):
        ids = dict(
            prova3asdfaaa1=0,
            prova3=1,
            prova2=2,
            prova=3,
            prova3asdfaa=4
        )
        for cid, cidv in ids.items():
            await self.publisher.put({'c': 'cmd', 'e_id': cidv, 'd': cid})

    def test(self):
        self.loop.run_until_complete(self.async_test())
        for i, msg in enumerate(self.messages):
            assert i == msg['e_id']
