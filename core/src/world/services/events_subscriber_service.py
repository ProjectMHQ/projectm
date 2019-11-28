import asyncio

import typing

from core.src.auth.logging_factory import LOGGER
from core.src.world.domain.area import Area
from core.src.world.entity import Entity
from core.src.world.services.redis_pubsub_service import PubSub


class RedisPubSubEventsSubscriberService:
    def __init__(self, pubsub: PubSub, loop=asyncio.get_event_loop()):
        self.pubsub = pubsub
        self._redis = None
        self._rooms_events_prefix = 'ev:r:'
        self._current_rooms_by_entity_id = dict()
        self._current_subscriptions_by_room = dict()
        self._tasks = dict()
        self.loop = loop
        self._observers_by_entity_id = dict()

    def add_observer_for_entity_id(self, entity_id, observer):
        if not self._observers_by_entity_id.get(entity_id):
            self._observers_by_entity_id[entity_id] = [observer]
        else:
            self._observers_by_entity_id[entity_id].append(observer)

    def pos_to_key(self, pos: typing.Tuple):
        return '{}:{}:{}:{}'.format(self._rooms_events_prefix, pos[0], pos[1], pos[2])

    def _get_current_rooms_by_entity_id(self, entity_id: int) -> typing.Set[typing.Tuple[int, int, int]]:
        current_rooms = self._current_rooms_by_entity_id.get(entity_id, dict())
        return set(current_rooms.keys())

    def _subscribe_rooms(self, entity: Entity, rooms: set):
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
            LOGGER.core.debug('Subscribing room %s', room)
            async for message in self.pubsub.subscribe(self.pos_to_key(room)):
                map(
                    lambda entity_id: self._on_new_message(entity_id, message),
                    self._current_subscriptions_by_room.get(room, {}).get('e', set())
                )
        finally:
            assert not self._current_subscriptions_by_room[room]['e']
            self._current_subscriptions_by_room.pop(room, None)
            LOGGER.core.debug('Unsubscribe room %s', room)

    def _unsubscribe_rooms(self, entity: Entity, rooms: set):
        for room in rooms:
            self._current_rooms_by_entity_id[entity.entity_id].pop(room)
            self._current_subscriptions_by_room[room]['e'].pop(entity.entity_id)

            if not self._current_subscriptions_by_room.get(room, {}).get('e', set()):
                task = self._current_subscriptions_by_room.get(room, {}).get('t', None)
                task and task.cancel()

    def _on_new_message(self, entity_id, message):
        for observer in self._observers_by_entity_id.get(entity_id, []):
            self.loop.create_task(observer.on_event(message))

    async def subscribe_area(self, entity: Entity, area: Area):
        current_rooms = self._get_current_rooms_by_entity_id(entity.entity_id)
        rooms_to_unsubscribe = current_rooms - area.rooms_coordinates
        rooms_to_subscribe = area.rooms_coordinates - current_rooms
        await asyncio.gather(
            self._subscribe_rooms(entity, rooms_to_subscribe),
            self._unsubscribe_rooms(entity, rooms_to_unsubscribe)
        )
