from enum import Enum

from aioredis import Redis


class EventType(Enum):
    ENTITY_LEFT_ROOM = 1
    ENTITY_JOIN_ROOM = 2
    ENTITY_DISAPPEAR_FROM_ROOM = 3
    ENTITY_APPEAR_IN_ROOM = 4
    ENTITY_DO_PUBLIC_ACTION = 5


class RedisPubSubEventsEmitterService:
    def __init__(self, redis_factory: callable):
        self.redis_factory = redis_factory
        self._redis = None
        self._prefix = 'ev:r:'

    async def redis(self) -> Redis:
        if not self._redis:
            self._redis = await self.redis_factory()
        return self._redis

    def pos_to_key(self, room_position):
        return self._prefix + room_position.x + ':' + room_position.y + ':' + room_position.z

    async def on_entity_left_room(self, entity, room_position):
        msg = {
            "r": [room_position.x, room_position.y, room_position.z]
            "en": entity.entity_id,
            "ev": EventType.ENTITY_LEFT_ROOM.value,
            "s": 1 # todo fixme
        }
        r = await self.redis()
        await r.publish_json(self.pos_to_key(room_position), msg)

    async def on_entity_join_room(self, entity, room_position):
        msg = {
            "r": [room_position.x, room_position.y, room_position.z]
            "en": entity.entity_id,
            "ev": EventType.ENTITY_JOIN_ROOM.value,
            "s": 1 # todo fixme
        }
        r = await self.redis()
        await r.publish_json(self.pos_to_key(room_position), msg)

    async def on_entity_disappear_from_room(self, entity, room_position):
        msg = {
            "r": [room_position.x, room_position.y, room_position.z]
            "en": entity.entity_id,
            "ev": EventType.ENTITY_DISAPPEAR_FROM_ROOM.value,
            "s": 1 # todo fixme
        }
        r = await self.redis()
        await r.publish_json(self.pos_to_key(room_position), msg)

    async def on_entity_appear_in_room(self, entity, room_position):
        msg = {
            "r": [room_position.x, room_position.y, room_position.z]
            "en": entity.entity_id,
            "ev": EventType.ENTITY_APPEAR_IN_ROOM.value,
            "s": 1 # todo fixme
        }
        r = await self.redis()
        await r.publish_json(self.pos_to_key(room_position), msg)

    async def on_entity_do_public_action(self, entity, room_position, action_public_message):
        msg = {
            "m": action_public_message,
            "en": entity.entity_id,
            "ev": EventType.ENTITY_DO_PUBLIC_ACTION.value,
            "s": 1 # todo fixme
        }
        r = await self.redis()
        await r.publish_json(self.pos_to_key(room_position), msg)

