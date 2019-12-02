import asyncio
from enum import Enum

import typing
from shapely.geometry import Point
from core.src.world.components.pos import PosComponent
from core.src.world.domain.area import Area
from core.src.world.entity import Entity
from core.src.world.services.redis_pubsub_publisher_service import PubSubEventType
from core.src.world.utils.world_types import EvaluatedEntity, Transport


class InterestType(Enum):
    NONE = 0
    LOCAL = 1
    REMOTE = 2


class PubSubObserver:
    def __init__(self, repository, transport, loop=asyncio.get_event_loop()):
        self.loop = loop
        self.repository = repository
        self.transport = transport

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

    async def on_event(self, entity_id: int, message: typing.Dict, room: typing.Tuple, transport_id: str):
        room = PosComponent(room)
        entity = Entity(entity_id)
        entity.transport = Transport(transport_id, self.transport)
        curr_pos = self.repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
        interest_type = await self._get_message_interest_type(entity, room, curr_pos)
        if not interest_type.value:
            return
        await self.publish_event(entity, message, room, interest_type, curr_pos)

    async def publish_event(self, entity: Entity, message, room, interest_type, curr_pos):
        who_what = (await self.repository.get_entities_evaluation_by_entity(entity.entity_id, message['en']))[0]
        self.loop.create_task(self._publish_message(entity, message, room, interest_type, who_what, curr_pos))
        self.loop.create_task(self._publish_system_event(entity, message, room, interest_type, who_what, curr_pos))

    async def _publish_system_event(self, entity, message, room, interest_type, who_what, current_position):
        payload = self._pubsub_event_to_transport_event(message, room, interest_type, who_what, current_position)
        payload and await entity.emit_msg(payload, topic="map")

    async def _publish_message(self, entity, message, room, interest_type, who_what, current_position):
        pass

    @staticmethod
    def _pubsub_event_to_transport_event(
            message, event_room, interest_type, entity: EvaluatedEntity, current_position
    ):
        area = Area(current_position)
        payload = {'data': {
            'e_id': message['en'],
            'type': entity.type,
        }}
        if interest_type == InterestType.LOCAL:
            payload['data'].update(
                {
                    'status': entity.status,
                    'excerpt': entity.excerpt,
                    'name': entity.known and entity.name
                }
            )
        if message['ev'] == PubSubEventType.ENTITY_APPEAR.value:
            payload['event'] = 'entity_add'
            payload['data']['rel_pos'] = area.get_relative_position(event_room)

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
                payload['data']['rel_pos'] = area.get_relative_position(event_room)
            elif current_distance <= max_distance and previous_distance <= max_distance:
                payload['event'] = 'entity_change_pos'
                payload['data']['rel_pos'] = area.get_relative_position(event_room)
            elif previous_distance == max_distance < current_distance:
                payload['event'] = 'entity_remove'
        else:
            raise ValueError('wut')
        return payload
