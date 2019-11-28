import typing

import time

from core.src.auth.logging_factory import LOGGER
from core.src.world.builder import map_repository
from core.src.world.components.pos import PosComponent


class Area:
    def __init__(self, center: PosComponent, square_size=15):
        self.center = center
        self.size = square_size
        self._rooms_coordinates = set()

    @property
    def rooms_coordinates(self) -> set:
        return self._rooms_coordinates

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

    async def get_rooms(self):
        res = []
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

                res.extend(data)
                assert len(data) == self.size, (len(data), from_x, to_x)
            else:
                res.extend([None] * self.size)
        return res

    async def get_map(self) -> typing.Dict:
        start = time.time()
        rooms = await self.get_rooms()
        LOGGER.websocket_monitor.debug('Rooms fetched in in %s', '{:.4f}'.format(time.time() - start))
        res = {'base': [], 'data': []}
        for index, r in enumerate(rooms):
            res['base'].append(r and r.terrain.value or 0)
            if r and r.content:
                for entry in r.content:
                    res['data'].append({'description': entry, 'pos': index})
        return res
