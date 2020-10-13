import asyncio
import time

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
        print('exists', res)
        return res

    async def save_library(self, data):
        redis = await self.redis()
        p = redis.pipeline()
        p.hmset(
            '{}:{}'.format(self._library_prefix, data['alias']), *self._flatten_dictionary(data)
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
        p.hmset(key, *self._flatten_dictionary(data))
        p.zadd(self._library_index, int(time.time()), data['alias'], exist=True)
        await p.execute()

    def _flatten_dictionary(self, d, prev_y=None, res=None):
        res = [] if res is None else res
        for y in d:
            if not prev_y:
                prev_y = y
            else:
                prev_y = '{}.{}'.format(prev_y, y)
            if isinstance(d[y], dict):
                self._flatten_dictionary(d[y], prev_y=prev_y, res=res)
            else:
                res.append(prev_y)
                res.append(d[y])
                #prev_y = prev_y and '.'.join(prev_y.split('.')[:-1])
            prev_y = prev_y and '.'.join(prev_y.split('.')[:-1])
        return res

    @staticmethod
    def _flattened_dictionary_to_entity(entity_data: dict):
        from core.src.world.components.factory import get_component_by_type
        from core.src.world.entity import Entity
        entity = Entity()
        entity.set(InstanceOfComponent(entity_data.pop(b'alias').decode()))
        for k, v in entity_data.items():
            k = k and k.decode()
            if isinstance(v, bytes):
                v = v.decode()
            if k.startswith('components.'):
                c = k.replace('components.', '').split('.')
                comp_type = get_component_by_type(c[0])
                if len(c) > 1:
                    if comp_type.key in entity.pending_changes:
                        entity.pending_changes[comp_type.key].add_component_value(c[1], v)
                    else:
                        entity.set(comp_type({c[1]: v}))
                else:
                    entity.set(comp_type(v))
        return entity

    async def get_libraries(self, pattern: str, offset=0, limit=20):
        pattern = pattern.replace('*', '\xff').encode()
        redis = await self.redis()
        entries = await redis.zrangebylex(self._library_index, max=pattern, offset=offset, count=limit)
        pipeline = redis.pipeline()
        for x in entries:
            pipeline.hmget('{}:{}'.format(
                self._library_prefix, x.decode()),
                'alias',
                'components.attributes.name'
            )
        result = await pipeline.execute()
        res = []
        for r in result:
            res.append(
                {
                    'alias': r[0].decode(),
                    'name': r[1].decode()
                }
            )
        return res

    async def get_instance_of(self, alias: str):
        redis = await self.redis()
        data = await redis.hgetall('{}:{}'.format(self._library_prefix, alias))
        if not data:
            return
        return self._flattened_dictionary_to_entity(data)
