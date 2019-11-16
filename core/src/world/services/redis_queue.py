import hashlib
import json

import typing
from aioredis import Redis


class RedisMultipleQueuesPublisher:
    def __init__(self, redis_factory: callable, num_queues: int):
        self.redis_factory = redis_factory
        self._redis = None
        self.num_queues = num_queues
        self.queue_prefix = 'rmq'

    async def redis(self) -> Redis:
        if not self._redis:
            self._redis = await self.redis_factory()
        return self._redis

    async def put(self, message: typing.Dict):
        entity_id = str(message['e_id'])
        queue = int.from_bytes(hashlib.sha256(entity_id.encode()).digest(), 'little') % self.num_queues
        redis = await self.redis()
        await redis.rpush(self.queue_prefix + str(queue), json.dumps(message))


class RedisQueueConsumer:
    def __init__(self,  redis_factory: callable, queue_id):
        self.redis_factory = redis_factory
        self._redis = None
        self.queue_key = 'rmq' + str(queue_id)

    async def redis(self) -> Redis:
        if not self._redis:
            self._redis = await self.redis_factory()
        return self._redis

    async def get(self, block=True, timeout=0):
        redis = await self.redis()
        if block:
            item = await redis.blpop(self.queue_key, timeout=timeout)
        else:
            item = await redis.lpop(self.queue_key)

        if item:
            item = item[1]
        return json.loads(item)

    async def qsize(self):
        redis = await self.redis()
        return await redis.llen(self.queue_key)

    async def empty(self):
        return await self.qsize() == 0
