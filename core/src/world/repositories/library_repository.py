import asyncio
import json
import time

import aioredis
import typing

from core.src.world.components.base import ComponentType
from core.src.world.components.factory import get_component_by_type
from core.src.world.components.system import SystemComponent
from core.src.world.domain.entity import Entity


class RedisLibraryRepository:
    def __init__(self, redis_factory: callable):
        self.redis_factory = redis_factory
        self.async_lock = asyncio.Lock()
        self._redis = None
        self._library_prefix = 'library'
        self._library_index = 'library:index'
        self._local_copy = dict()
        self._sorted_library_keys = []

    async def redis(self) -> aioredis.Redis:
        await self.async_lock.acquire()
        try:
            if not self._redis:
                self._redis = await self.redis_factory()
        finally:
            self.async_lock.release()
        return self._redis

    async def exists(self, libname: str):
        redis = await self.redis()
        res = await redis.hexists(self._library_prefix, libname)
        return res

    async def save_library_item(self, data):
        redis = await self.redis()
        data['created_at'] = int(time.time())
        assert not await redis.hexists(self._library_prefix, data['libname'])
        pipeline = redis.pipeline()
        pipeline.hset(self._library_prefix, data['libname'], json.dumps(data))
        pipeline.zadd(self._library_index, int(time.time()), data['libname'])
        await pipeline.execute()
        await self._on_item_added(data)

    async def update_library_item(self, data):
        redis = await self.redis()
        assert await redis.hexists(self._library_prefix, data['libname'])
        pipeline = redis.pipeline()
        pipeline.hset(self._library_prefix, data['libname'], json.dumps(data))
        pipeline.zadd(self._library_index, int(time.time()), data['libname'], exist=True)
        await pipeline.execute()
        await self._on_item_updated(data)

    async def remove_library_item(self, name: str):
        redis = await self.redis()
        pipeline = redis.pipeline()
        pipeline.hdel(self._library_prefix, name)
        pipeline.zrem(self._library_index, name)
        await pipeline.execute()
        await self._on_item_removed(name)

    async def build(self):
        redis = await self.redis()
        pipeline = redis.pipeline()
        pipeline.hgetall(self._library_prefix)
        pipeline.zrange(self._library_index, 0, 99999999999999)
        data = await pipeline.execute()
        assert len(data[0]) == len(data[1]), (data[0], data[1])
        for key, value in data[0].items():
            self._local_copy[key.decode()] = json.loads(value)
        self._sorted_library_keys = [k.decode() for k in data[1]]
        return self

    async def _on_item_added(self, data: typing.Dict):
        assert data['libname'] not in self._local_copy
        self._local_copy[data['libname']] = data
        self._sorted_library_keys.append(data['libname'])

    async def _on_item_updated(self, data: typing.Dict):
        assert data['libname'] in self._local_copy
        self._local_copy[data['libname']] = data

    async def _on_item_removed(self, name: str):
        self._local_copy.pop(name)
        self._sorted_library_keys.remove(name)

    async def on_item_add_received(self, name: str):
        redis = await self.redis()
        data = await redis.hget(self._library_prefix, name)
        await self._on_item_added(json.loads(data))

    async def on_item_update_received(self, name: str):
        redis = await self.redis()
        data = await redis.hget(self._library_prefix, name)
        await self._on_item_updated(json.loads(data))

    async def on_item_remove_received(self, name: str):
        await self._on_item_removed(name)

    def get_instance_of(self, name: str, entity: Entity) -> typing.Optional[Entity]:
        e = Entity()
        data = self._local_copy.get(name)
        if not data:
            return

        system_component = SystemComponent()\
            .instance_of.set(data['libname'])\
            .created_at.set(int(time.time()))\
            .instance_by.set(entity.entity_id)

        e.set_for_update(system_component)
        for component in data['components']:
            comp_type = get_component_by_type(component)
            if comp_type.has_data():
                e.set_for_update(comp_type().activate())
        return e

    def get_libraries(self, pattern: str, offset=0, limit=20):
        if '*' in pattern:
            if not pattern.endswith('*'):
                return []
            pattern = pattern.replace('*', '')
        else:
            data = self._local_copy.get(pattern)
            return data and [data] or []
        res = []
        skipped = 0
        for k in self._sorted_library_keys:
            if k.startswith(pattern):
                if skipped < offset:
                    skipped += 1
                    continue
                res.append(self._local_copy[k])
            if len(res) == limit:
                break
        return res

    def get_defaults_for_library_element(self, name: str, component: typing.Type[ComponentType]) -> ComponentType:
        assert name
        val = self._local_copy.get(name, {'components': {}})['components'].get(component.libname)
        return val and component(val)
