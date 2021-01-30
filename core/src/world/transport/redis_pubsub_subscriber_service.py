import asyncio

from core.src.auth.logging_factory import LOGGER
from core.src.world.services.redis_pubsub_interface import PubSubManager


class RedisPubSubSystemEventsSubscriberService:
    def __init__(self, pubsub: PubSubManager, loop=asyncio.get_event_loop()):
        self.pubsub = pubsub
        self._redis = None
        self.loop = loop
        self._observers_by_topic = {}
        self._current_subscriptions_by_topic = {}

    def add_observer_for_topic(self, topic: str, observer):
        self._observers_by_topic[topic] = observer

    async def _subscribe_pubsub_topic(self, topic):
        try:
            async for message in self.pubsub.subscribe(topic):
                LOGGER.core.debug('RECEIVED SYSTEM MESSAGE %s', message)
                self.loop.create_task(self._observers_by_topic[topic].on_event(topic, message))

        finally:
            await self._handle_subscribe_cancel(topic)

    async def _handle_subscribe_cancel(self, topic):
        if self._observers_by_topic.get(topic):
            self._current_subscriptions_by_topic[topic] = {
                't': self.loop.create_task(self._subscribe_pubsub_topic(topic)),
            }
        else:
            self._current_subscriptions_by_topic.pop(topic, None)
            await self.pubsub.unsubscribe(topic)

    async def subscribe_transport_system_messages(self):
        topic = 'system.transport'
        assert self._observers_by_topic.get(topic)
        assert not self._current_subscriptions_by_topic.get(topic)
        self._current_subscriptions_by_topic[topic] = {
            't': self.loop.create_task(self._subscribe_pubsub_topic(topic)),
        }
