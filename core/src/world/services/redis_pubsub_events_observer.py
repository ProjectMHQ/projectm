import asyncio
from enum import Enum

import typing

from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.position import PositionComponent
from core.src.world.components.system import SystemComponent
from core.src.world.domain.area import Area
from core.src.world.domain.entity import Entity
from core.src.world.services.redis_pubsub_publisher_service import PubSubEventType
from core.src.world.utils.entity_utils import load_components
from core.src.world.utils.messaging import emit_sys_msg


class InterestType(Enum):
    NONE = 0
    LOCAL = 1
    REMOTE = 2


class PubSubObserver:
    def __init__(self, repository, loop=asyncio.get_event_loop()):
        self.loop = loop
        self.repository = repository
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
    def _entity_sees_it(message: typing.Dict, current_position):
        _pos = [current_position.x, current_position.y, current_position.z]
        return bool(message['curr'] == _pos) or bool(message['prev'] == _pos)

    @staticmethod
    def _is_system_event(message: typing.Dict):
        value = bool(
            PubSubEventType(message['ev']) in [
                PubSubEventType.ENTITY_APPEAR,
                PubSubEventType.ENTITY_DISAPPEAR,
                PubSubEventType.ENTITY_CHANGE_POS
            ]
        )
        return value

    @staticmethod
    def _is_public_action(message: typing.Dict):
        return bool(PubSubEventType(message['ev']) == PubSubEventType.ENTITY_DO_PUBLIC_ACTION)

    @staticmethod
    def _is_appearance_message(message):
        return bool(
            PubSubEventType(message['ev']) in (
                PubSubEventType.ENTITY_APPEAR,
                PubSubEventType.ENTITY_DISAPPEAR
            )
        )

    async def on_event(self, entity_id: int, message: typing.Dict, room: typing.Tuple, transport_id: str):
        room = PositionComponent(coord='{},{},{}'.format(*room))
        entity = Entity(entity_id).set_component(SystemComponent().connection.set(transport_id))
        await load_components(entity, PositionComponent)
        curr_pos = entity.get_component(PositionComponent)
        interest_type = await self._get_message_interest_type(entity, room, curr_pos)
        if not interest_type.value:
            return
        await self.publish_event(entity, message, room, interest_type, curr_pos)

    async def publish_event(self, entity: Entity, message, room, interest_type, curr_pos):
        if self._is_system_event(message):
            event = self._get_system_event(message, room, curr_pos)
            self.loop.create_task(emit_sys_msg(entity, None, event))

        if self._is_movement_message(message):
            if self._entity_sees_it(message, curr_pos):
                payload = await self._get_character_movement_message(
                    entity, message, interest_type, curr_pos
                )
                if payload['action'] == 'leave':
                    for observer in self.postprocessed_events_observers.get('follow', []):
                        self.loop.create_task(observer.on_event(payload))
        elif self._is_appearance_message(message):
            print('TODO DO CONNECT ACTION MESSAGE')
        else:
            raise ValueError('wtfff? %s' % message)

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
        evaluated_emitter_entity = await load_components(Entity(message['en']), AttributesComponent)
        payload = {
                "event": "move",
                "entity": {
                    "name": evaluated_emitter_entity.get_component(AttributesComponent).name,
                    "id": message['en']
                },
                'from': message['prev'],
                'to': message['curr']
            }
        if message['curr'] == curr_pos.list_coordinates:
            assert message['prev'] != curr_pos
            assert interest_type == InterestType.LOCAL
            payload['action'] = "join"
            payload['direction'] = self._gather_movement_direction(message, "join")
        elif message['prev'] == curr_pos.list_coordinates:
            assert message['curr'] != curr_pos
            assert interest_type != InterestType.LOCAL
            payload['action'] = "leave"
            payload['direction'] = self._gather_movement_direction(message, "leave")
        else:
            raise ValueError('This should not be here: %s (%s)' % (message, curr_pos.value))
        return payload
