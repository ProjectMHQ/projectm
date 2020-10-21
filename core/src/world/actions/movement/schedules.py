import typing

from core.src.world.actions.movement.movement_messages import MovementMessages
from core.src.world.components.pos import PosComponent
from core.src.world.domain.entity import Entity
from core.src.world.domain.room import Room
from core.src.world.utils.world_types import DirectionEnum
from core.src.world.utils.world_utils import direction_to_coords_delta, apply_delta_to_position, get_room_at_direction

messages = MovementMessages()


class ScheduledMovement:
    def __init__(self, entity: Entity, direction: DirectionEnum, target: Room, escape_corners=False):
        self._carambole = {
            DirectionEnum.NORTH: [DirectionEnum.EAST, DirectionEnum.WEST],
            DirectionEnum.SOUTH: [DirectionEnum.EAST, DirectionEnum.WEST],
            DirectionEnum.EAST: [DirectionEnum.NORTH, DirectionEnum.SOUTH],
            DirectionEnum.WEST: [DirectionEnum.NORTH, DirectionEnum.SOUTH],
            DirectionEnum.UP: [],
            DirectionEnum.DOWN: []
        }
        self.entity = entity
        self.escape_corners = escape_corners
        self.direction = direction
        self.target_room = target

    async def find_escape(self) -> typing.Optional[Room]:
        from core.src.world.builder import map_repository
        escapes = self._carambole[self.direction]
        rooms = []
        for escape in escapes:
            delta = direction_to_coords_delta(escape)
            target_position = apply_delta_to_position(self.entity.get_room().position, delta)
            _room = await map_repository.get_room(target_position, populate=False)
            if _room and await _room.walkable_by(self.entity):
                rooms.append([escape, _room])
        if len(rooms) != 1:
            return
        self.direction = rooms[0][0]
        return rooms[0][1]

    async def do(self) -> bool:
        from core.src.world.actions.movement.move import do_move_entity
        if not self.entity.get_room():
            position = self.entity.get_component(PosComponent)
            assert position
            self.entity.set_room(Room(position))
        if not self.target_room:
            self.target_room = await get_room_at_direction(self.entity, self.direction, populate=False)
        if not await self.target_room.walkable_by(self.entity):
            new_target = self.escape_corners and await self.find_escape()
            if new_target:
                self.target_room = new_target
            else:
                await self.entity.emit_msg(messages.invalid_direction())
                return False
        await do_move_entity(self.entity, self.target_room, self.direction, "movement")
        self.target_room = None
        return True

    async def stop(self):
        pass

    async def impossible(self):
        pass