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
    async def _get_message_interest_type(room, curr_pos):
        if curr_pos.z != room.z and (curr_pos.x == room.x) and (curr_pos.y == room.y):
            distance = abs(curr_pos.z - room.z)
        elif curr_pos.z != room.z:
            return InterestType.NONE
        else:
            distance = int(Point(curr_pos.x, curr_pos.y).distance(Point(room.x, room.y)))
        if not distance:
            return InterestType.LOCAL
        elif distance in (1, 2):
            return InterestType.REMOTE
        else:
            return InterestType.NONE

    async def on_event(self, entity_id: int, message: typing.Dict, room: typing.Tuple, transport_id: str):
        room = PosComponent(room)
        entity = Entity(entity_id)
        entity.transport = Transport(transport_id, self.transport)
        curr_pos = self.repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
        interest_type = await self._get_message_interest_type(room, curr_pos)
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
    def _pubsub_event_to_transport_event(message, room, interest_type, entity: EvaluatedEntity, current_position):
        payload = {'data': {}}
        if interest_type == InterestType.LOCAL:
            payload['data'].update(
                {
                    'status': entity.status,
                    'excerpt': entity.excerpt,
                    'name': entity.known and entity.name
                }
            )
        if message['ev'] not in (
            PubSubEventType.ENTITY_APPEAR.value,
            PubSubEventType.ENTITY_DISAPPEAR.value,
            PubSubEventType.ENTITY_CHANGE_POS.value
        ):
            return None

        payload['data'].update(
            {
                'e_id': message['en'],
                'type': entity.type,
            }

        )
        rel_area = Area(current_position)
        rel_pos = rel_area.get_relative_position(room)
        prev_rel_pos = Area(current_position).get_relative_position(current_position)
        array_size = (rel_area.size ** 2) - 1
        if (0 < rel_pos < array_size) and (0 < prev_rel_pos < array_size):
            payload['event'] = 'entity_change_pos'
            payload['data']['rel_pos'] = rel_pos
        elif (0 < rel_pos < array_size) and not (0 < prev_rel_pos < array_size):
            payload['event'] = 'entity_add'
            payload['data']['rel_pos'] = rel_pos
        elif not (0 < rel_pos < array_size) and (0 < prev_rel_pos < array_size):
            payload['event'] = 'entity_remove'
        else:
            raise ValueError(
                'Doh, rel_pos: %s, prev_rel_pos: %s' % (rel_pos, prev_rel_pos)
            )
        return payload
