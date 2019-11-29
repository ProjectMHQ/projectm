import asyncio
from enum import Enum

import typing
from shapely.geometry import Point
from core.src.world.components.pos import PosComponent
from core.src.world.domain.area import Area
from core.src.world.entity import Entity
from core.src.world.services.redis_pubsub_publisher_service import PubSubEventType
from core.src.world.utils.world_types import EvaluatedEntity


class InterestType(Enum):
    NONE = 0
    LOCAL = 1
    REMOTE = 2


class PubSubObserver:
    def __init__(self, loop=asyncio.get_event_loop()):
        self.loop = loop

    @staticmethod
    async def _get_message_interest_type(room, curr_pos):
        if curr_pos.z != room.z and (curr_pos.x == room.x) and (curr_pos.y == room.y):
            distance = abs(curr_pos.z - room.z)
        else:
            distance = int(Point(curr_pos.x, curr_pos.y).distance(Point(room.x, room.y)))
        if not distance:
            return InterestType.LOCAL
        elif distance in (1, 2):
            return InterestType.REMOTE
        else:
            return InterestType.NONE

    async def on_event(self, entity: Entity, message: typing.Dict, room):
        from core.src.world.builder import world_repository
        curr_pos = world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
        interest_type = await self._get_message_interest_type(room, curr_pos)
        if not interest_type.value:
            return
        await self.publish_event(entity, message, room, interest_type, curr_pos)

    async def publish_event(self, entity: Entity, message, room, interest_type, curr_pos):
        who_what = await entity.recognize_entities(message['en_id'])[0]
        self.loop.create_task(self._publish_message(entity, message, room, interest_type, who_what, curr_pos))
        self.loop.create_task(self._publish_system_event(entity, message, room, interest_type, who_what, curr_pos))

    async def _publish_system_event(self, entity, message, room, interest_type, who_what, current_position):
        topic, payload = self._pubsub_event_to_transport_event(message, room, interest_type, who_what, current_position)
        await entity.emit_msg(payload, topic=topic)

    async def _publish_message(self, entity, message, room, interest_type, who_what, current_position):
        pass

    @staticmethod
    def _pubsub_event_to_transport_event(message, room, interest_type, who_what: EvaluatedEntity, current_position):
        payload = {}
        if interest_type == InterestType.LOCAL:
            payload.update(
                {
                    'status': who_what.status,
                    'description': who_what.description,
                    'name': who_what.known and who_what.name
                }
            )
        if message['ev'] in (
            PubSubEventType.ENTITY_APPEAR_IN_ROOM.value,
            PubSubEventType.ENTITY_JOIN_ROOM.value
        ):
            topic = 'map'
            payload.update(
                {
                    'event': 'entity_new_pos',
                    'e_id': message['en_id'],
                    'rel_pos': Area(current_position).get_relative_position(room),
                    'type': who_what.type,
                }
            )
        else:
            raise ValueError
        return topic, payload
