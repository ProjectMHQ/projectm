import asyncio
from enum import Enum

import typing
from shapely.geometry import Point
from core.src.world.components.pos import PosComponent
from core.src.world.entity import Entity


class InterestType(Enum):
    NONE = 0
    LOCAL = 1
    REMOTE = 2


class PubSubObserver:
    def __init__(self, loop=asyncio.get_event_loop()):
        self._commands = {}
        self.loop = loop
        self.translator = None

    def add_messages_translator(self, translator):
        self.translator = translator
        return self

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
        self.loop.create_task(self._publish_message(message, room, interest_type, who_what, curr_pos))
        self.loop.create_task(self._publish_system_event(message, room, interest_type, who_what, curr_pos))

    async def _publish_message(self, message, room, interest_type, who_what, current_position):
        pass

    async def _publish_system_event(self, message, room, interest_type, who_what, current_position):
        pass
