import asyncio
import json
import time
from ast import literal_eval

import aioredis

from core.src.world.components.instance_of import InstanceOfComponent


class RedisLibraryRepository:
    def __init__(self, redis_factory: callable):
        self.redis_factory = redis_factory
        self.async_lock = asyncio.Lock()
        self._redis = None
        self._library_prefix = 'lib'
        self._library_index = 'index:lib'

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
        res = await redis.exists('{}:{}'.format(self._library_prefix, alias))
        return res

    async def save_library(self, data):
        redis = await self.redis()
        p = redis.pipeline()
        y = ['alias', data['alias']]
        for k, v in data['components'].items():
            if isinstance(v, (list, dict)):
                v = json.dumps(v)
            y.extend([k, v])
        p.hmset(
            '{}:{}'.format(self._library_prefix, data['alias']), *y
        )
        p.zadd(
            self._library_index, int(time.time()), data['alias']
        )
        await p.execute()

    async def update_library(self, data):
        redis = await self.redis()
        p = redis.pipeline()
        key = '{}:{}'.format(self._library_prefix, data['alias'])
        p.delete(key)
        y = ['alias', data['alias']]
        for k, v in data['components'].items():
            if isinstance(v, (list, dict)):
                v = json.dumps(v)
            y.extend([k, v])
        p.hmset(
            '{}:{}'.format(self._library_prefix, data['alias']), *y
        )
        p.zadd(self._library_index, int(time.time()), data['alias'], exist=True)
        await p.execute()

    async def get_libraries(self, pattern: str, offset=0, limit=20):
        pattern = pattern.replace('*', '\xff').encode()
        redis = await self.redis()
        entries = await redis.zrangebylex(self._library_index, max=pattern, offset=offset, count=limit)
        pipeline = redis.pipeline()
        for x in entries:
            pipeline.hmget('{}:{}'.format(self._library_prefix, x.decode()), 'alias',  'attributes')
        result = await pipeline.execute()
        res = []
        for r in result:
            res.append(
                {
                    'alias': r[0].decode(),
                    'name': literal_eval(r[1].decode())['name']
                }
            )
        return res

    async def get_instance_of(self, alias: str):
        from core.src.world.components.factory import get_component_by_type
        from core.src.world.entity import Entity
        redis = await self.redis()
        data = await redis.hgetall('{}:{}'.format(self._library_prefix, alias))
        if not data:
            return
        e = Entity()
        for k, v in data.items():
            k = k.decode()
            if k != 'alias':
                comp = get_component_by_type(k)
                c = comp.from_bytes(v) if comp.component_type in (dict, list) else comp(v.decode())
                e.set(c)
        e.set(InstanceOfComponent(data[b'alias'].decode()))
        return e
