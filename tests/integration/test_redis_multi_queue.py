import asyncio
from unittest import TestCase

from core.src.world.services.redis_queue import RedisMultipleQueuesPublisher, RedisQueueConsumer
from core.src.world.utils import async_redis_pool_factory


class TestRedisMultiQueue(TestCase):
    def setUp(self):
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
            await self.publisher.put(cid, {'message': cid})
            self.assertEqual(await self.consumers[cidv].get(), {'message': cid})

    def test(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_test())
