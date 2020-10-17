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

    def _eid_to_key(self, entity_id: int):
        return 'chan:{}'.format(entity_id)

    async def on_entity_change_position(self, entity, room_position, reason, targets=[]):
        """
        MUST be fired AFTER the the entity position is changed.
        """
        msg = {
            "en": entity.entity_id,
            "entity_type": 0,
            "reason": reason,
            "ev": PubSubEventType.ENTITY_CHANGE_POS.value,
            "curr": room_position.value,
            "prev": room_position.previous_position.value
        }
        for target in targets:
            k = self._eid_to_key(target)
            LOGGER.core.debug('Publishing Message %s on channel %s', msg, k)
            await self.pubsub.publish(k, msg)

    async def on_entity_appear_position(self, entity, room_position, reason, targets):
        msg = {
            "en": entity.entity_id,
            "entity_type": 0,
            "reason": reason,
            "ev": PubSubEventType.ENTITY_APPEAR.value,
            "curr": room_position.value
        }
        for target in targets:
            k = self._eid_to_key(target)
            LOGGER.core.debug('Publishing Message %s on channels %s', msg, k)
            await self.pubsub.publish(k, msg)

    async def on_entity_disappear_position(self, entity, room_position, reason, targets):
        msg = {
            "en": entity.entity_id,
            "entity_type": 0,
            "reason": reason,
            "ev": PubSubEventType.ENTITY_DISAPPEAR.value,
            "curr": room_position.value
        }
        for target in targets:
            k = self._eid_to_key(target)
            LOGGER.core.debug('Publishing Message %s on channels %s', msg, k)
            await self.pubsub.publish(k, msg)

    async def on_entity_do_public_action(
            self, entity, room_position, action_public_payload: typing.Dict, target: int
    ):
        msg = {
            "p": action_public_payload,
            "entity_type": 0,
            "en": entity.entity_id,
            "ev": PubSubEventType.ENTITY_DO_PUBLIC_ACTION.value,
            "target": target,
            "curr": room_position.value
        }
        k = self._eid_to_key(target)
        LOGGER.core.debug('Publishing Message %s on channel %s', msg, k)
        await self.pubsub.publish(k, msg)

    async def on_entity_quit_world(self, entity):
        msg = {
            "en": entity.entity_id,
            "ev": PubSubEventType.ENTITY_QUIT.value,
        }
        LOGGER.core.debug('Publishing Message %s on system queue', msg)
        await self.pubsub.publish('system.transport', msg)
