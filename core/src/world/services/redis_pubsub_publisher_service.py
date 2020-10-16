from enum import Enum
import typing

from core.src.auth.logging_factory import LOGGER
from core.src.world.services.redis_pubsub_interface import PubSubManager


class PubSubEventType(Enum):
    ENTITY_CHANGE_POS = 1
    ENTITY_DISAPPEAR = 2
    ENTITY_APPEAR = 3
    ENTITY_DO_PUBLIC_ACTION = 4
    ENTITY_QUIT = 5


class RedisPubSubEventsPublisherService:
    def __init__(self, pubsub: PubSubManager):
        self.pubsub = pubsub
        self._redis = None
        self._rooms_events_prefix = 'ev:r'

    def pos_to_key(self, pos):
        return '{}:{}:{}:{}'.format(self._rooms_events_prefix, pos.x, pos.y, pos.z)

    async def on_entity_change_position(self, entity, room_position, reason, targets=[]):
        """
        MUST be fired AFTER the the entity position is changed.
        """
        msg = {
            "en": entity.entity_id,
            "entity_type": 0,
            "reason": reason,
            "ev": PubSubEventType.ENTITY_CHANGE_POS.value,
            "curr": [room_position.x, room_position.y, room_position.z],
            "prev": [
                room_position.previous_position.x,
                room_position.previous_position.y,
                room_position.previous_position.z
            ]
        }
        for target in targets:
            room_key = self.pos_to_key(target)
            LOGGER.core.debug('Publishing Message %s on channel %s', msg, room_key)
            await self.pubsub.publish(room_key, msg)

    async def on_entity_appear_position(self, entity, room_position, reason, targets=[]):
        msg = {
            "en": entity.entity_id,
            "entity_type": 0,
            "reason": reason,
            "ev": PubSubEventType.ENTITY_APPEAR.value,
            "curr": [room_position.x, room_position.y, room_position.z],
        }
        for target in targets:
            room_key = self.pos_to_key(target)
            LOGGER.core.debug('Publishing Message %s on channels %s', msg, room_key)
            await self.pubsub.publish(room_key, msg)

    async def on_entity_disappear_position(self, entity, room_position, reason, targets=[]):
        msg = {
            "en": entity.entity_id,
            "entity_type": 0,
            "reason": reason,
            "ev": PubSubEventType.ENTITY_DISAPPEAR.value,
            "curr": [room_position.x, room_position.y, room_position.z],
        }
        for target in targets:
            room_key = self.pos_to_key(target)
            LOGGER.core.debug('Publishing Message %s on channels %s', msg, room_key)
            await self.pubsub.publish(room_key, msg)

    async def on_entity_do_public_action(
            self, entity, room_position, action_public_payload: typing.Dict, target: int, targets=[]
    ):
        msg = {
            "p": action_public_payload,
            "entity_type": 0,
            "en": entity.entity_id,
            "ev": PubSubEventType.ENTITY_DO_PUBLIC_ACTION.value,
            "target": target,
            "curr": room_position
        }
        for t in targets:
            room_key = self.pos_to_key(t)
            LOGGER.core.debug('Publishing Message %s on channel %s', msg, room_key)
            await self.pubsub.publish(room_key, msg)

    async def on_entity_quit_world(self, entity, room_position):
        msg = {
            "en": entity.entity_id,
            "ev": PubSubEventType.ENTITY_QUIT.value,
            "curr": room_position
        }
        LOGGER.core.debug('Publishing Message %s on system queue', msg)
        await self.pubsub.publish('system.transport', msg)
