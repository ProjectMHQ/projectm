import typing

import time

from core.src.auth.logging_factory import LOGGER
from core.src.world.components.pos import PosComponent

from core.src.world.domain.room import Room
from core.src.world.entity import Entity


class Area:
    def __init__(self, center: PosComponent, square_size=9):
        self.center = center
        self.size = square_size
        self.rooms: typing.List[typing.Optional[Room]] = []
        self._rooms_coordinates = set()
        self._peripheral_coordinates = set()

    @property
    def rooms_coordinates(self) -> set:
        return self._rooms_coordinates

    @property
    def rooms_and_peripherals_coordinates(self) -> set:
        return self._rooms_coordinates | self._peripheral_coordinates

    @property
    def min_x(self) -> int:
        return self.center.x - int(self.size / 2)

    @property
    def max_x(self) -> int:
        return self.center.x + int(self.size / 2)

    @property
    def min_y(self) -> int:
        return self.center.y - int(self.size / 2) - self.size % 2

    @property
    def max_y(self) -> int:
        return self.center.y + int(self.size / 2)

    def make_coordinates(self):
        from core.src.world.builder import map_repository
        from_x = max([self.min_x, map_repository.min_x])
        to_x = min([self.max_x, map_repository.max_x])
        for y in range(self.max_y, self.min_y, -1):
            if map_repository.min_y < y < map_repository.max_y:
                if to_x < map_repository.max_x:
                    self._peripheral_coordinates.add((to_x + 1, y, self.center.z))
                if from_x > map_repository.min_x:
                    self._peripheral_coordinates.add((from_x - 1, y, self.center.z))
            for x in range(from_x, to_x + 1):
                self._rooms_coordinates.add((x, y, self.center.z))
                if (y == self.min_y + 1) and y > map_repository.min_y:
                    self._peripheral_coordinates.add((x, y - 1, self.center.z))
                elif (y == self.max_y) and y < map_repository.max_y:
                    self._peripheral_coordinates.add((x, y + 1, self.center.z))
        return self

    async def get_rooms(self):
        if not self.rooms:
            await self.populate_rooms()
        return self.rooms

    async def get_map(self, pov: Entity=None) -> typing.Dict:
        start = time.time()
        rooms = await self.get_rooms()
        LOGGER.websocket_monitor.debug('Rooms fetched in in %s', '{:.4f}'.format(time.time() - start))
        res = {'base': [], 'data': []}
        for index, r in enumerate(rooms):
            res['base'].append(r and r.terrain.value or 0)
            if r and r.content:
                for entry in r.content:
                    if pov and entry.entity_id == pov.entity_id:
                        continue
                    payload = {
                        'type': entry.type,
                        'pos': index,
                        'e_id': entry.entity_id
                    }
                    res['data'].append(payload)
        return res

    def is_position_inside(self, pos: PosComponent):
        if pos.z != self.center.z:
            return False
        max_distance = self.size // 2
        distance = int(
            max([abs(self.center.x - pos.x), abs(self.center.y - pos.y)])
        )
        return bool(distance <= max_distance)

    def get_relative_position(self, position: PosComponent) -> int:
        return (self.max_y - position.y) * (self.max_x - self.min_x + 1) + position.x - self.min_x

    async def populate_rooms(self):
        from core.src.world.builder import map_repository
        from_x = max([self.min_x, map_repository.min_x])
        to_x = min([self.max_x, map_repository.max_x])
        for y in range(self.max_y, self.min_y, -1):
            for x in range(from_x, to_x + 1):
                self._rooms_coordinates.add((x, y, self.center.z))
            if map_repository.min_y <= y <= map_repository.max_y:
                data = await map_repository.get_rooms_on_y(y, from_x, to_x + 1, self.center.z)

                if self.min_x <= map_repository.min_x:
                    data = ([None] * (self.size - len(data))) + data

                if self.max_x >= map_repository.max_x:
                    data = data + ([None] * (self.size - len(data)))

                self.rooms.extend(data)
                assert len(data) == self.size, (len(data), from_x, to_x)
            else:
                self.rooms.extend([None] * self.size)
        return self

    async def populate_rooms_content(self, entity: Entity):
        from core.src.world.builder import world_repository
        await world_repository.populate_area_content_for_area(entity, self)
        return self

    async def get_map_for_entity(self, entity: Entity) -> typing.Dict:
        await self.populate_rooms()
        await self.populate_rooms_content(entity)
        return await self.get_map(pov=entity)
