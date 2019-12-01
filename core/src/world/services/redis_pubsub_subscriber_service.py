import asyncio

import typing

from core.src.auth.logging_factory import LOGGER
from core.src.world.components.pos import PosComponent
from core.src.world.domain.area import Area
from core.src.world.entity import Entity
from core.src.world.services.redis_pubsub_interface import PubSubManager


class RedisPubSubEventsSubscriberService:
    def __init__(self, pubsub: PubSubManager, loop=asyncio.get_event_loop()):
        self.pubsub = pubsub
        self._redis = None
        self._rooms_events_prefix = 'ev:r'
        self._current_rooms_by_entity_id = dict()
        self._current_subscriptions_by_room = dict()
        self._tasks = dict()
        self.loop = loop
        self._observers_by_entity_id = dict()
        self._transports_by_entity_id = dict()

    def pos_to_key(self, pos: typing.Tuple):
        return '{}:{}:{}:{}'.format(self._rooms_events_prefix, pos[0], pos[1], pos[2])

    def _get_current_rooms_by_entity_id(self, entity_id: int) -> typing.Set[typing.Tuple[int, int, int]]:
        current_rooms = self._current_rooms_by_entity_id.get(entity_id, set())
        return set(current_rooms)

    async def _subscribe_rooms(self, entity: Entity, rooms: set):
        if not self._current_rooms_by_entity_id.get(entity.entity_id):
            self._current_rooms_by_entity_id[entity.entity_id] = rooms
        else:
            self._current_rooms_by_entity_id[entity.entity_id].update(rooms)

        for room in rooms:
            if not self._current_subscriptions_by_room.get(room):
                self._current_subscriptions_by_room[room] = {
                    't': self.loop.create_task(self._subscribe_pubsub_topic(room)),
                    'e': {entity.entity_id}
                }
            else:
                self._current_subscriptions_by_room[room]['e'].add(entity.entity_id)

    async def _subscribe_pubsub_topic(self, room):
        try:
            async for message in self.pubsub.subscribe(self.pos_to_key(room)):
                LOGGER.core.debug('RECEIVED MESSAGE %s', message)
                for entity_id in self._current_subscriptions_by_room.get(room, {}).get('e', set()):
                    message['en'] != entity_id and self._on_new_message(entity_id, message, room)
        finally:
            assert not self._current_subscriptions_by_room[room]['e']
            self._current_subscriptions_by_room.pop(room, None)
            await self.pubsub.unsubscribe(self.pos_to_key(room))

    async def _unsubscribe_rooms(self, entity: Entity, rooms: set):
        for room in rooms:
            self._current_rooms_by_entity_id[entity.entity_id].remove(room)
            self._current_subscriptions_by_room[room]['e'].remove(entity.entity_id)

            if not self._current_subscriptions_by_room.get(room, {}).get('e', set()):
                task = self._current_subscriptions_by_room.get(room, {}).get('t', None)
                task and task.cancel()
        if not self._current_rooms_by_entity_id.get(entity.entity_id):
            self._current_rooms_by_entity_id.pop(entity.entity_id, None)

    def _on_new_message(self, entity_id, message, room):
        for observer in self._observers_by_entity_id.get(entity_id, []):
            LOGGER.core.debug('MESSAGE for entity_id %s: %s', entity_id, message)
            self.loop.create_task(
                observer.on_event(entity_id, message, room, self._transports_by_entity_id[entity_id])
            )

    async def subscribe_area(self, entity: Entity, area: Area):
        self._transports_by_entity_id[entity.entity_id] = entity.transport.namespace
        LOGGER.core.debug('Entity %s subscribed Area with center %s', entity.entity_id, area.center)
        current_rooms = self._get_current_rooms_by_entity_id(entity.entity_id)
        rooms_to_unsubscribe = current_rooms - area.rooms_coordinates
        rooms_to_subscribe = area.rooms_coordinates - current_rooms
        await asyncio.gather(
            self._subscribe_rooms(entity, rooms_to_subscribe),
            self._unsubscribe_rooms(entity, rooms_to_unsubscribe)
        )

    async def bootstrap_subscribes(self, data: typing.Dict[Entity, typing.List[int]]):
        for en, pos_val in data.items():
            pos_val and await self._subscribe_rooms(
                Entity(en),
                Area(PosComponent(pos_val)).make_coordinates().rooms_coordinates
            )
        print('Subscribed ', data.keys())

    async def unsubscribe_all(self, entity: Entity):
        current_rooms = self._get_current_rooms_by_entity_id(entity.entity_id)
        self._transports_by_entity_id.pop(entity.entity_id, None)
        await self._unsubscribe_rooms(entity, current_rooms)

    def add_observer_for_entity_id(self, entity_id, observer):
        if not self._observers_by_entity_id.get(entity_id):
            self._observers_by_entity_id[entity_id] = [observer]
        else:
            self._observers_by_entity_id[entity_id].append(observer)

    def remove_observer_for_entity_id(self, entity_id):
        self._observers_by_entity_id.pop(entity_id, None)
