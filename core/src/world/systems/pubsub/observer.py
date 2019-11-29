from enum import Enum
from shapely.geometry import Point
from core.src.world.components.pos import PosComponent
from core.src.world.entity import Entity


class InterestType(Enum):
    NONE = 0
    LOCAL = 1
    REMOTE = 2


class PubSubObserver:
    def __init__(self, entity: Entity):
        self._commands = {}
        self._entity = entity

    async def _get_message_interest_type(self, room):
        # FIXME TODO - Cache entity
        from core.src.world.builder import world_repository
        curr_pos = world_repository.get_component_value_by_entity_id(self._entity.entity_id, PosComponent)
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

    async def on_event(self, message, room):
        interest_type = await self._get_message_interest_type(room)
        if not interest_type.value:
            return
        await self.publish_event(message, room)

    async def publish_event(self):
        raise NotImplementedError
