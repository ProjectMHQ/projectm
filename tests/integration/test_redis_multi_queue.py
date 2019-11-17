from etc import settings
import asyncio
from unittest import TestCase
from core.src.auth.builder import strict_redis
from core.src.world.services.redis_queue import RedisMultipleQueuesPublisher, RedisQueueConsumer
from core.src.world.services.worker_queue_service import WorkerQueueService
from core.src.world.services.system_utils import get_redis_factory, RedisType


class TestRedisMultiQueue(TestCase):
    def setUp(self):
        assert settings.INTEGRATION_TESTS
        assert settings.RUNNING_TESTS
        strict_redis.flushdb()
        self.loop = asyncio.get_event_loop()
        self.publisher = RedisMultipleQueuesPublisher(
            get_redis_factory(RedisType.QUEUES),
            num_queues=5
        )
        self.consumers = [
            RedisQueueConsumer(get_redis_factory(RedisType.QUEUES), x) for x in range(0, 5)
        ]

    async def async_test(self):
        ids = {
            1: 0,
            2: 1,
            4: 2,
            3: 3,
            7: 4
        }
        for cid, cidv in ids.items():
            await self.publisher.put({'message': cid, 'e_id': cid, 'c': 'cmd'})
            self.assertEqual(await self.consumers[cidv].get(), {'message': cid, 'e_id': cid, 'c': 'cmd'})

    def test(self):
        self.loop.run_until_complete(self.async_test())


class TestRedisWorkerQueueService(TestCase):
    def setUp(self):
        self.messages = []
        strict_redis.flushdb()
        self.loop = asyncio.get_event_loop()
        self.publisher = RedisMultipleQueuesPublisher(
            get_redis_factory(RedisType.QUEUES),
            num_queues=5
        )
        self.workers = [
            WorkerQueueService(
                self.loop,
                RedisQueueConsumer(get_redis_factory(RedisType.QUEUES), x)
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
            worker.add_queue_observer('cmd', self.observers[i])

    async def on_message(self, message):
        self.messages.append(message)

    async def dummy(self):
        return

    async def async_test(self):
        ids = {
            1: 0,
            2: 1,
            4: 2,
            3: 3,
            7: 4
        }
        for cid, cidv in ids.items():
            await self.publisher.put({'c': 'cmd', 'e_id': cid, 'd': cidv})
        await asyncio.sleep(0.5)

    def test(self):
        ids = {0, 1, 2, 3, 4}
        self.loop.run_until_complete(self.async_test())
        for m in self.messages:
            ids.remove(m['d'])
        self.assertEqual(set(), ids)
