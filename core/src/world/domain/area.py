import asyncio

from core.src.world.builder import map_repository
from core.src.world.components.pos import PosComponent


class Area:
    def __init__(self, center: PosComponent, square_size=9):
        self.center = center
        self.size = square_size

    @property
    def min_x(self):
        return self.center.x - int(self.size / 2) - self.size % 2

    @property
    def max_x(self):
        return self.center.x + int(self.size / 2)

    @property
    def min_y(self):
        return self.center.y - int(self.size / 2) - self.size % 2

    @property
    def max_y(self):
        return self.center.y + int(self.size / 2) + self.size % 2

    async def get_rooms(self):
        res = []
        from_y = max([self.min_y, map_repository.min_y])
        to_y = min([self.max_y, map_repository.max_y])
        for x in range(self.min_x, self.max_x):
            if x >= map_repository.min_x:
                data = await map_repository.get_rooms_on_y(x, from_y, to_y, self.center.z)
                if map_repository.min_y > from_y:
                    data = ([None] * (from_y - map_repository.min_y)) + data
                if to_y > map_repository.max_y:
                    data = data + ([None] * (to_y - map_repository.max_y))
                res.extend(data)
            else:
                res.extend([None] * self.size)
        return res

    async def get_map(self):
        rooms = await self.get_rooms()
        res = {'base': [], 'data': []}
        for i, r in enumerate(rooms):
            res['base'].append(r and r.terrain.value or 0)
            if r and r.content:
                res['data'].append({'descr': r.content[-1], 'pos': i})
        return res


if __name__ == '__main__':
    size = 9
    a = Area(center=PosComponent([3, 2, 0]), square_size=size)
    loop = asyncio.get_event_loop()
    q = [(x and x.terrain.value or 0) for x in loop.run_until_complete(a.get_rooms())]
    p = ""
    c = {
        0: " ",
        1: "#",
        2: "."
    }
    for i in range(size, len(q), size):
        p += "".join([c[x] for x in q[i-size:i]]) + '\n'
    print(p)
