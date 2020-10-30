import asyncio
import typing
from core.src.auth.logging_factory import LOGGER
from core.src.world.components.system import SystemComponent
from core.src.world.domain.entity import Entity
from core.src.world.services.redis_pubsub_interface import PubSubManager


class RedisPubSubEventsSubscriberService:
    def __init__(self, pubsub: PubSubManager, loop=asyncio.get_event_loop()):
        self.pubsub = pubsub
        self._redis = None
        self._current_subscriptions_by_entity_id = dict()
        self._tasks = dict()
        self.loop = loop
        self._observers_by_entity_id = dict()
        self._transports_by_entity_id = dict()

    async def _subscribe_entity(self, entity: Entity):
        if not self._current_subscriptions_by_entity_id.get(entity.entity_id):
            self._current_subscriptions_by_entity_id[entity.entity_id] = {
                't': self.loop.create_task(self._subscribe_pubsub_topic(entity.entity_id)),
                'e': {entity.entity_id}
            }

    def _eid_to_key(self, entity_id: int):
        return 'chan:{}'.format(entity_id)

    async def _subscribe_pubsub_topic(self, entity_id: int):
        async for message in self.pubsub.subscribe(self._eid_to_key(entity_id)):
            self._on_new_message(entity_id, message)

    def _on_new_message(self, entity_id, message):
        for observer in self._observers_by_entity_id.get(entity_id, []):
            LOGGER.core.debug('MESSAGE for entity_id %s: %s', entity_id, message)
            self.loop.create_task(
                observer.on_event(
                    entity_id,
                    message,
                    message['curr'],
                    self._transports_by_entity_id[entity_id]
                )
            )

    async def subscribe_events(self, entity: Entity):
        connection = entity.get_component(SystemComponent).connection
        assert connection.value
        self._transports_by_entity_id[entity.entity_id] = connection.value
        await asyncio.gather(self._subscribe_entity(entity))

    async def bootstrap_subscribes(self, data: typing.List[typing.Dict]):
        for en in data:
            await self.subscribe_events(
                Entity(en['entity_id']).set_component(SystemComponent(connection=en['channel_id']))
            )

    async def unsubscribe_all(self, entity: Entity):
        self._transports_by_entity_id.pop(entity.entity_id, None)
        await self._unsubscribe_entity(entity.entity_id)

    async def _unsubscribe_entity(self, entity_id: int):
        res = self._current_subscriptions_by_entity_id.pop(entity_id, None)
        if res:
            task = res.get('t', None)
            task and task.cancel()

    def add_observer_for_entity_id(self, entity_id: int, observer):
        self._observers_by_entity_id[entity_id] = [observer]
            
    def add_observer_for_entity_data(self, entity_data: typing.Dict, observer):
        self._transports_by_entity_id[entity_data['entity_id']] = entity_data['channel_id']
        self.add_observer_for_entity_id(entity_data['entity_id'], observer)

    def remove_observer_for_entity_id(self, entity_id):
        self._observers_by_entity_id.pop(entity_id, None)
