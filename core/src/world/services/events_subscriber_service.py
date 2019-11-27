import asyncio

import typing
from aioredis import Redis

from core.src.world.domain.area import Area
from core.src.world.entity import Entity


class RedisPubSubEventsSubscriberService:
    def __init__(self, redis_factory: callable, loop=asyncio.get_event_loop()):
        self.redis_factory = redis_factory
        self._redis = None
        self._rooms_events_prefix = 'ev:r:'
        self._current_rooms = {}
        self.loop = loop

    async def redis(self) -> Redis:
        if not self._redis:
            self._redis = await self.redis_factory()
        return self._redis

    def pos_to_key(self, pos: typing.Tuple):
        return '{}:{}:{}:{}'.format(self._rooms_events_prefix, pos[0], pos[1], pos[2])

    async def unsubscribe_room(self, coords: typing.Tuple):
        pass

    async def subscribe_area(self, entity: Entity, area: Area):
        current_rooms = self._current_rooms.get(entity.entity_id, set())
        new_rooms = set()
        for x in range(area.min_x, area.max_x+1):
            for y in range(area.min_y, area.max_y+1):
                new_rooms.add((x, y, area.center.z))

        r = await self.redis()
        self.loop.create_task(r.unsubscribe(*(self.pos_to_key(c) for c in current_rooms - new_rooms)))
        self.loop.create_task(r.subscribe(*(self.pos_to_key(c) for c in new_rooms - current_rooms)))
