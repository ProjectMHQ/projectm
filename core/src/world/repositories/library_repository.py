import asyncio

import aioredis


class RedisLibraryRepository:
    def __init__(self, redis_factory: callable):
        self.redis_factory = redis_factory
        self.async_lock = asyncio.Lock()
        self._redis = None
        self._library_prefix = 'lib'

    async def redis(self) -> aioredis.Redis:
        await self.async_lock.acquire()
        try:
            if not self._redis:
                self._redis = await self.redis_factory()
        finally:
            self.async_lock.release()
        return self._redis

    async def exists(self, alias: str):
        redis = await self.redis()
        return redis.keys('{}:{}'.format(self._library_prefix, alias))

