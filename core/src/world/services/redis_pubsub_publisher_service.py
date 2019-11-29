import asyncio
from enum import Enum
import typing
from core.src.world.services.redis_pubsub_interface import PubSubManager


class PubSubEventType(Enum):
    ENTITY_LEFT_ROOM = 1
    ENTITY_JOIN_ROOM = 2
    ENTITY_DISAPPEAR_FROM_ROOM = 3
    ENTITY_APPEAR_IN_ROOM = 4
    ENTITY_DO_PUBLIC_ACTION = 5


class RedisPubSubEventsPublisherService:
    def __init__(self, pubsub: PubSubManager):
        self.pubsub = pubsub
        self._redis = None
        self._rooms_events_prefix = 'ev:r'

    def pos_to_key(self, pos):
        return '{}:{}:{}:{}'.format(self._rooms_events_prefix, pos.x, pos.y, pos.z)

    async def on_entity_change_position(self, entity, room_position, previous_position):
        msg = {
            "en": entity.entity_id,
            "ev": PubSubEventType.ENTITY_JOIN_ROOM.value,
            "curr": [room_position.x, room_position.y, room_position.z],
            "prev": [previous_position.x, previous_position.y, previous_position.z]
        }
        await asyncio.gather(
            self.pubsub.publish(self.pos_to_key(room_position), msg),
            self.pubsub.publish(self.pos_to_key(previous_position), msg)
        )

    async def on_entity_do_public_action(self, entity, room_position, action_public_payload: typing.Dict):
        msg = {
            "p": action_public_payload,
            "en": entity.entity_id,
            "ev": PubSubEventType.ENTITY_DO_PUBLIC_ACTION.value,
        }
        await self.pubsub.publish(self.pos_to_key(room_position), msg)
