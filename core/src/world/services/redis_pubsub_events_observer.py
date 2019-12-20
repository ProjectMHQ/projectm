import asyncio
from enum import Enum

import typing
from core.src.world.components.pos import PosComponent
from core.src.world.domain.area import Area
from core.src.world.entity import Entity, EntityID
from core.src.world.services.redis_pubsub_publisher_service import PubSubEventType
from core.src.world.utils.world_types import Transport


class InterestType(Enum):
    NONE = 0
    LOCAL = 1
    REMOTE = 2


class PubSubObserver:
    def __init__(self, repository, transport, translator, loop=asyncio.get_event_loop()):
        self.loop = loop
        self.repository = repository
        self.transport = transport
        self.messages_translator = translator
        self.postprocessed_events_observers = {}

    def add_observer_for_pov_event(self, event_type: str, observer):
        if not self.postprocessed_events_observers.get(event_type):
            self.postprocessed_events_observers[event_type] = [observer]
        else:
            self.postprocessed_events_observers[event_type].append(observer)

    @staticmethod
    def _gather_movement_direction(message: typing.Dict, action):
        join = bool(action == 'join')
        if message['curr'][0] > message['prev'][0]:
            return join and 'w' or 'e'
        elif message['curr'][0] < message['prev'][0]:
            return join and 'e' or 'w'
        elif message['curr'][1] > message['prev'][1]:
            return join and 's' or 'n'
        elif message['curr'][1] < message['prev'][1]:
            return join and 'n' or 's'
        elif message['curr'][2] > message['prev'][2]:
            return join and 'u' or 'd'
        elif message['curr'][2] < message['prev'][2]:
            return join and 'd' or 'u'
        else:
            raise ValueError('Unable to gather movement direction for message: %s' % message)

    @staticmethod
    async def _get_message_interest_type(entity, room, curr_pos):
        if curr_pos.z != room.z and (curr_pos.x == room.x) and (curr_pos.y == room.y):
            distance = abs(curr_pos.z - room.z)
        else:
            distance = int(
                max([abs(curr_pos.x - room.x), abs(curr_pos.y - room.y)])
            )
        if not distance:
            return InterestType.LOCAL
        elif distance < entity.get_view_size():
            return InterestType.REMOTE
        else:
            return InterestType.NONE

    @staticmethod
    def _is_movement_message(message: typing.Dict):
        return bool(message.get("reason") == "movement")

    @staticmethod
    def _is_a_character_movement(message: typing.Dict):
        return bool(message['entity_type'] in (0, ))

    @staticmethod
    def _entity_sees_it(message: typing.Dict, current_position: PosComponent):
        _pos = [current_position.x, current_position.y, current_position.z]
        return bool(message['curr'] == _pos) or bool(message['prev'] == _pos)

    @staticmethod
    def _is_system_event(message: typing.Dict):
        return bool(
            PubSubEventType(message['ev']) in [
                PubSubEventType.ENTITY_APPEAR,
                PubSubEventType.ENTITY_DISAPPEAR,
                PubSubEventType.ENTITY_CHANGE_POS
            ]
        )

    @staticmethod
    def _is_public_action(message: typing.Dict):
        return bool(message['ev'] == PubSubEventType.ENTITY_DO_PUBLIC_ACTION.value)

    async def on_event(self, entity_id: int, message: typing.Dict, room: typing.Tuple, transport_id: str):
        room = PosComponent(room)
        entity = Entity(EntityID(entity_id))
        entity.transport = Transport(transport_id, self.transport)
        curr_pos = await self.repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
        interest_type = await self._get_message_interest_type(entity, room, curr_pos)
        if not interest_type.value:
            return
        await self.publish_event(entity, message, room, interest_type, curr_pos)

    async def publish_event(self, entity: Entity, message, room, interest_type, curr_pos):
        if self._is_system_event(message):
            event = self._get_system_event(message, room, curr_pos)
            self.loop.create_task(entity.emit_system_event(event))

        if self._is_movement_message(message):
            if self._entity_sees_it(message, curr_pos):
                payload = await self._get_character_movement_message(
                    entity, message, interest_type, curr_pos
                )
                message = self.messages_translator.event_msg_to_string(payload, 'msg')
                self.loop.create_task(entity.emit_msg(message))
                if payload['action'] == 'leave':
                    for observer in self.postprocessed_events_observers.get('follow', []):
                        print('observerone!!!')
                        self.loop.create_task(observer.on_event(payload))
        else:
            if interest_type == InterestType.LOCAL:
                if self._is_public_action(message):
                    payload = await self._get_public_action_message(
                        entity, message, interest_type
                    )
                    message = self.messages_translator.event_msg_to_string(payload, 'msg')
                    self.loop.create_task(entity.emit_msg(message))

    @staticmethod
    def _get_system_event(message, event_room, current_position):
        area = Area(current_position)
        payload = {'data': {
            'e_id': message['en']
        }}
        if message['ev'] == PubSubEventType.ENTITY_APPEAR.value:
            payload['event'] = 'entity_add'
            payload['data']['type'] = message['entity_type']
            payload['data']['pos'] = area.get_relative_position(event_room)

        elif message['ev'] == PubSubEventType.ENTITY_DISAPPEAR.value:
            payload['event'] = 'entity_remove'

        elif message['ev'] == PubSubEventType.ENTITY_CHANGE_POS.value:
            area = Area(current_position)
            max_distance = int(area.size / 2)
            current_distance = int(max(
                [abs(area.center.x - message['curr'][0]), abs(area.center.y - message['curr'][1])]
            ))
            previous_distance = int(max(
                [abs(area.center.x - message['prev'][0]), abs(area.center.y - message['prev'][1])]
            ))
            if current_distance <= max_distance < previous_distance:
                payload['event'] = 'entity_add'
                payload['data']['pos'] = area.get_relative_position(event_room)
            elif current_distance <= max_distance and previous_distance <= max_distance:
                payload['event'] = 'entity_change_pos'
                payload['data']['pos'] = area.get_relative_position(event_room)
            elif previous_distance == max_distance < current_distance:
                payload['event'] = 'entity_remove'
        else:
            raise ValueError('wut is %s' % message)
        return payload

    async def _get_character_movement_message(self, entity, message, interest_type, curr_pos) -> typing.Dict:
        assert interest_type
        evaluated_emitter_entity = (
            await self.repository.get_entities_evaluation_by_entity(entity.entity_id, message['en'])
        )[0]
        payload = {
                "event": "move",
                "entity": {
                    "excerpt": evaluated_emitter_entity.excerpt,
                    "name": evaluated_emitter_entity.known and evaluated_emitter_entity.name,
                    "id": message['en']
                },
                'from': message['prev'],
                'to': message['curr']
            }
        if message['curr'] == curr_pos.value:
            assert message['prev'] != curr_pos
            assert interest_type == InterestType.LOCAL
            payload['action'] = "join"
            payload['direction'] = self._gather_movement_direction(message, "join")
        elif message['prev'] == curr_pos.value:
            assert message['curr'] != curr_pos
            assert interest_type != InterestType.LOCAL
            payload['action'] = "leave"
            payload['direction'] = self._gather_movement_direction(message, "leave")
        else:
            raise ValueError('This should not be here: %s (%s)' % (message, curr_pos.value))
        return payload

    async def _get_public_action_message(self, entity, message, interest_type):
        assert interest_type.LOCAL
        evaluated_emitter_entity = (
            await self.repository.get_entities_evaluation_by_entity(entity.entity_id, message['en'])
        )[0]
        payload = {
            "event": "look",
            "origin": {
                "excerpt": evaluated_emitter_entity.excerpt,
                "name": evaluated_emitter_entity.known and evaluated_emitter_entity.name,
                "id": message['en'],
                "known": True
            }
        }
        if message['target'] == entity.entity_id:
            payload['target'] = 'self'
        else:
            evaluated_target_entity = (
                await self.repository.get_entities_evaluation_by_entity(entity.entity_id, message['target'])
            )[0]
            payload['target'] = {
                "excerpt": evaluated_target_entity.excerpt,
                "name": evaluated_target_entity.known and evaluated_target_entity.name,
                "id": message['target'],
                "known": True
            }
        return payload
