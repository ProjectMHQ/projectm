from enum import Enum

import typing

from core.src.world.services.redis_pubsub_interface import PubSub


class EventType(Enum):
    ENTITY_LEFT_ROOM = 1
    ENTITY_JOIN_ROOM = 2
    ENTITY_DISAPPEAR_FROM_ROOM = 3
    ENTITY_APPEAR_IN_ROOM = 4
    ENTITY_DO_PUBLIC_ACTION = 5


class RedisPubSubEventsPublisherService:
    def __init__(self, pubsub: PubSub):
        self.pubsub = pubsub
        self._redis = None
        self._rooms_events_prefix = 'ev:r'

    def pos_to_key(self, pos):
        return '{}:{}:{}:{}'.format(self._rooms_events_prefix, pos.x, pos.y, pos.z)

    async def on_entity_left_room(self, entity, room_position):
        msg = {
            "en": entity.entity_id,
            "ev": EventType.ENTITY_LEFT_ROOM.value,
            "s": 1  # todo fixme
        }
        await self.pubsub.publish(self.pos_to_key(room_position), msg)

    async def on_entity_join_room(self, entity, room_position):
        msg = {
            "en": entity.entity_id,
            "ev": EventType.ENTITY_JOIN_ROOM.value,
            "s": 1  # todo fixme
        }
        await self.pubsub.publish(self.pos_to_key(room_position), msg)

    async def on_entity_disappear_from_room(self, entity, room_position):
        msg = {
            "en": entity.entity_id,
            "ev": EventType.ENTITY_DISAPPEAR_FROM_ROOM.value,
            "s": 1  # todo fixme
        }
        await self.pubsub.publish(self.pos_to_key(room_position), msg)

    async def on_entity_appear_in_room(self, entity, room_position):
        msg = {
            "en": entity.entity_id,
            "ev": EventType.ENTITY_APPEAR_IN_ROOM.value,
            "s": 1  # todo fixme
        }
        await self.pubsub.publish(self.pos_to_key(room_position), msg)

    async def on_entity_do_public_action(self, entity, room_position, action_public_payload: typing.Dict):
        msg = {
            "p": action_public_payload,
            "en": entity.entity_id,
            "ev": EventType.ENTITY_DO_PUBLIC_ACTION.value,
            "s": 1  # todo fixme
        }
        await self.pubsub.publish(self.pos_to_key(room_position), msg)

