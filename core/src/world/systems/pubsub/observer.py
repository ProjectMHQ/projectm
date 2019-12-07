import asyncio
from enum import Enum

import typing
from shapely.geometry import Point
from core.src.world.components.pos import PosComponent
from core.src.world.domain.area import Area
from core.src.world.entity import Entity
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

    @staticmethod
    def _gather_movement_direction(message: typing.Dict):
        if message['curr'][0] > message['prev'][0]:
            return 'w'
        elif message['curr'][0] < message['prev'][0]:
            return 'e'
        elif message['curr'][1] > message['prev'][1]:
            return 'n'
        elif message['curr'][1] < message['prev'][1]:
            return 's'
        elif message['curr'][2] > message['prev'][2]:
            return 'u'
        elif message['curr'][2] < message['prev'][2]:
            return 'd'
        else:
            raise ValueError('Unable to gather movement direction for message: %s' % message)

    @staticmethod
    async def _get_message_interest_type(entity, room, curr_pos):
        if curr_pos.z != room.z and (curr_pos.x == room.x) and (curr_pos.y == room.y):
            distance = abs(curr_pos.z - room.z)
        else:
            distance = int(Point(curr_pos.x, curr_pos.y).distance(Point(room.x, room.y)))
        if not distance:
            return InterestType.LOCAL
        elif distance < entity.get_view_size():
            return InterestType.REMOTE
        else:
            return InterestType.NONE

    @staticmethod
    def _is_movement_message(message: typing.Dict):
        return bool(message["reason"] == "movement")

    @staticmethod
    def _is_a_character_movement(message: typing.Dict):
        return bool(message['entity_type'] in (0, ))

    @staticmethod
    def _entity_sees_it(message: typing.Dict, current_position: PosComponent):
        return bool(
            message['curr'] == current_position
        ) or bool(
            message['prev'] == current_position
        )

    async def on_event(self, entity_id: int, message: typing.Dict, room: typing.Tuple, transport_id: str):
        room = PosComponent(room)
        entity = Entity(entity_id)
        entity.transport = Transport(transport_id, self.transport)
        curr_pos = await self.repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
        interest_type = await self._get_message_interest_type(entity, room, curr_pos)
        if not interest_type.value:
            return
        await self.publish_event(entity, message, room, interest_type, curr_pos)

    async def publish_event(self, entity: Entity, message, room, interest_type, curr_pos):

        # FIXME TODO \\ NOT EFFICIENT
        # FIXME TODO \\ Remove Evaluated Entity Concept, use character_memory map and embed emitter info
        # FIXME TODO \\ into the event itself.

        evaluated_emitter_entity = interest_type == InterestType.LOCAL and (
            await self.repository.get_entities_evaluation_by_entity(entity.entity_id, message['en'])
        )[0]

        event = self._get_system_event(message, room, curr_pos, evaluated_emitter_entity)
        self.loop.create_task(entity.emit_system_event(event))

        if self._is_movement_message(message) and self._entity_sees_it(message, curr_pos):
            if self._is_a_character_movement(message):
                payload = self._get_character_movement_message(
                    message, interest_type, curr_pos, evaluated_emitter_entity
                )
                message = self.messages_translator.event_msg_to_string(payload, 'msg')
                self.loop.create_task(entity.emit_msg(message))

    @staticmethod
    def _get_system_event(message, event_room, current_position, evaluated_emitter_entity):
        area = Area(current_position)
        payload = {'data': {
            'e_id': message['en']
        }}
        if evaluated_emitter_entity:
            payload['data'].update(
                {
                    'status': evaluated_emitter_entity.status,
                    'excerpt': evaluated_emitter_entity.excerpt,
                    'name': evaluated_emitter_entity.known and evaluated_emitter_entity.name
                }
            )
        if message['ev'] == PubSubEventType.ENTITY_APPEAR.value:
            payload['event'] = 'entity_add'
            payload['data']['type'] = message['entity_type']
            payload['data']['pos'] = area.get_relative_position(event_room)

        elif message['ev'] == PubSubEventType.ENTITY_DISAPPEAR.value:
            payload['event'] = 'entity_remove'

        elif message['ev'] == PubSubEventType.ENTITY_CHANGE_POS.value:
            area = Area(current_position)
            center_point = Point(area.center.x, area.center.y, area.center.z)
            max_distance = int(area.size / 2)
            current_distance = int(
                center_point.distance(Point(event_room.x, event_room.y, event_room.z))
            )
            previous_distance = int(
                center_point.distance(Point(message['prev'][0], message['prev'][1], message['prev'][2]))
            )
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

    def _get_character_movement_message(
            self, message, interest_type, curr_pos, evaluated_emitter_entity
    ) -> typing.Dict:
        assert interest_type
        payload = {
                "entity": {
                    "excerpt": evaluated_emitter_entity.excerpt,
                    "name": evaluated_emitter_entity.known and evaluated_emitter_entity.name,
                    "id": message['en']
                }
            }
        if message['curr'] == curr_pos.value:
            assert message['prev'] != curr_pos
            assert interest_type == InterestType.LOCAL
            payload['action'] = "join"
        elif message['prev'] != curr_pos.value:
            assert message['cur'] != curr_pos
            assert interest_type == InterestType.LOCAL
            payload['action'] = "leave"
        else:
            raise ValueError('This should not be here: %s' % message)
        payload['direction'] = self._gather_movement_direction(message)
        return payload
