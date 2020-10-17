import asyncio
from enum import IntEnum
import aioredis
import typing


class DescriptionType(IntEnum):
    ENTITY = 0
    TERRAIN = 1


class RedisDescriptionsRepository:
    def __init__(self, redis_factory: callable):
        self.redis_factory = redis_factory
        self.prefix = 'd'
        self.terrain_suffix = 'r'
        self.entity_suffix = 'e'
        self._redis = None
        self.async_lock = asyncio.Lock()

    async def redis(self) -> aioredis.Redis:
        await self.async_lock.acquire()
        try:
            if not self._redis:
                self._redis = await self.redis_factory()
        finally:
            self.async_lock.release()
        return self._redis

    async def save_entity_description(self, entity_id: int, title: str, description: str) -> typing.Dict:
        await self._save_description(DescriptionType.ENTITY, entity_id, title, description)
        return {
            "entity_id": entity_id,
            "title": title,
            "description": description
        }

    async def save_terrain_description(self, terrain_id, title: str, description: str) -> typing.Dict:
        await self._save_description(DescriptionType.TERRAIN, terrain_id, title, description)
        return {
            "terrain_id": terrain_id,
            "title": title,
            "description": description
        }

    async def get_entity_description(self, entity_id: int) -> typing.Optional[typing.Dict]:
        res = await self._get_description(DescriptionType.ENTITY, entity_id)
        if not res:
            return
        return {
            "entity_id": entity_id,
            "title": res[0],
            "description": res[1]
        }

    async def get_terrain_description(self, terrain_id: int) -> typing.Optional[typing.Dict]:
        res = await self._get_description(DescriptionType.TERRAIN, terrain_id)
        if not res:
            return
        return {
            "terrain_id": terrain_id,
            "title": res[0],
            "description": res[1]
        }

    async def get_all_terrains_descriptions(self) -> typing.Dict:
        redis = await self.redis()
        res = {}
        x = await redis.hscan('{}:{}'.format(self.prefix, self.terrain_suffix))
        for key, value in x[1]:
            value = value.decode().split('|SEP|')
            res[int(key.decode())] = {'title': value[0], 'description': value[1]}
        return res

    async def _save_description(
        self,
        description_type: DescriptionType,
        target_id: int,
        title: str,
        description: str
    ):
        redis = await self.redis()
        if description_type == DescriptionType.TERRAIN:
            collection = '{}:{}'.format(self.prefix, self.terrain_suffix)
        elif description_type == DescriptionType.ENTITY:
            collection = '{}:{}'.format(self.prefix, self.entity_suffix)
        else:
            raise ValueError('wtf')
        await redis.hset(collection, str(target_id), '{}|SEP|{}'.format(title, description))

    async def _get_description(self, description_type: DescriptionType, identifier: int):
        redis = await self.redis()
        if description_type == DescriptionType.TERRAIN:
            collection = '{}:{}'.format(self.prefix, self.terrain_suffix)
        elif description_type == DescriptionType.ENTITY:
            collection = '{}:{}'.format(self.prefix, self.entity_suffix)
        else:
            raise ValueError('wtf')
        res = await redis.hget(collection, str(identifier))
        if res:
            title, description = res.decode().split('|SEP|')
            return title, description
