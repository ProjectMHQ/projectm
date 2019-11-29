import asyncio
from enum import Enum
import typing

from core.src.auth.logging_factory import LOGGER
from core.src.world.services.redis_pubsub_interface import PubSubManager


class PubSubEventType(Enum):
    ENTITY_CHANGE_POS = 1
    ENTITY_DISAPPEAR = 2
    ENTITY_APPEAR = 3
    ENTITY_DO_PUBLIC_ACTION = 4


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
            "ev": PubSubEventType.ENTITY_CHANGE_POS.value,
            "curr": [room_position.x, room_position.y, room_position.z],
            "prev": [previous_position.x, previous_position.y, previous_position.z]
        }
        room_key = self.pos_to_key(room_position)
        prev_room_key = self.pos_to_key(previous_position)
        LOGGER.core.debug('Publishing Message %s on channels %s %s', msg, room_key, prev_room_key)
        await self.pubsub.publish(room_key, msg)

    async def on_entity_do_public_action(self, entity, room_position, action_public_payload: typing.Dict):
        msg = {
            "p": action_public_payload,
            "en": entity.entity_id,
            "ev": PubSubEventType.ENTITY_DO_PUBLIC_ACTION.value,
        }
        room_key = self.pos_to_key(room_position)
        LOGGER.core.debug('Publishing Message %s on channel %s', msg, room_key)
        await self.pubsub.publish(room_key, msg)
