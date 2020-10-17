import asyncio

import typing

from core.src.auth.logging_factory import LOGGER
from core.src.world.components.pos import PosComponent
from core.src.world.domain.area import Area
from core.src.world.domain.entity import Entity, EntityID
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
            await self._handle_subscribe_cancel(room)

    async def _handle_subscribe_cancel(self, room):
        stale_entities = set()
        if self._current_subscriptions_by_room[room]['e']:
            for e in self._current_subscriptions_by_room[room]['e']:
                if room not in self._current_rooms_by_entity_id[e]:
                    stale_entities.add(e)
                    LOGGER.core.error('Stale entity, weird behaviour or race condition')
            self._current_subscriptions_by_room[room] = {
                't': self.loop.create_task(self._subscribe_pubsub_topic(room)),
                'e': self._current_subscriptions_by_room[room]['e'] - stale_entities
            }
        else:
            self._current_subscriptions_by_room.pop(room, None)
            await self.pubsub.unsubscribe(self.pos_to_key(room))

    async def _unsubscribe_rooms(self, entity: Entity, rooms: set):
        for room in rooms:
            self._current_rooms_by_entity_id[entity.entity_id].remove(room)
            self._current_subscriptions_by_room[room]['e'].remove(entity.entity_id)

            if not self._current_subscriptions_by_room[room]['e']:
                task = self._current_subscriptions_by_room.get(room, {}).get('t', None)
                task and task.cancel()
        if not self._current_rooms_by_entity_id.get(entity.entity_id):
            self._current_rooms_by_entity_id.pop(entity.entity_id, None)

    def _on_new_message(self, entity_id, message, room):
        for observer in self._observers_by_entity_id.get(entity_id, []):
            LOGGER.core.debug('MESSAGE for entity_id %s: %s', entity_id, message)
            self.loop.create_task(
                observer.on_event(
                    entity_id, message, message['curr'], self._transports_by_entity_id[entity_id].namespace
                )
            )

    async def subscribe_area(self, entity: Entity, area: Area):
        self._transports_by_entity_id[entity.entity_id] = entity.transport
        current_rooms = self._get_current_rooms_by_entity_id(entity.entity_id)
        rooms_to_unsubscribe = current_rooms - {(area.center.x, area.center.y, area.center.z)}
        rooms_to_subscribe = {(area.center.x, area.center.y, area.center.z)} - current_rooms
        LOGGER.core.debug(
            'Entity %s subscribed Area with center %s. Rooms to subscribe: %s, rooms to unsubscribe: %s',
            entity.entity_id, area.center, rooms_to_subscribe, rooms_to_unsubscribe
        )
        await asyncio.gather(
            self._subscribe_rooms(entity, rooms_to_subscribe),
            self._unsubscribe_rooms(entity, rooms_to_unsubscribe)
        )

    async def bootstrap_subscribes(self, data: typing.Dict[int, typing.List[int]]):
        for en, pos_val in data.items():
            LOGGER.core.debug('Entity %s subscribed Area with center %s', en, pos_val)
            area = Area(PosComponent(pos_val))
            LOGGER.core.debug(
                'Entity %s subscribed Area with center %s - Total %s subs',
                en, pos_val, len(area.rooms_and_peripherals_coordinates)
            )
            pos_val and await self._subscribe_rooms(
                Entity(EntityID(en)),
                {(area.center.x, area.center.y, area.center.z)}
            )

    async def unsubscribe_all(self, entity: Entity):
        current_rooms = self._get_current_rooms_by_entity_id(entity.entity_id)
        self._transports_by_entity_id.pop(entity.entity_id, None)
        await self._unsubscribe_rooms(entity, current_rooms)

    def add_observer_for_entity_id(self, entity_id: int, observer):
        self._observers_by_entity_id[entity_id] = [observer]
            
    def add_observer_for_entity_data(self, entity_data: typing.Dict, observer):
        self._transports_by_entity_id[entity_data['entity_id']] = entity_data['transport']
        self.add_observer_for_entity_id(entity_data['entity_id'], observer)

    def remove_observer_for_entity_id(self, entity_id):
        self._observers_by_entity_id.pop(entity_id, None)
