import asyncio

from core.src.world.builder import map_repository
from core.src.world.components.pos import PosComponent


class Area:
    def __init__(self, center: PosComponent, square_size=9):
        self.center = center
        self.size = square_size

    @property
    def min_x(self):
        return self.center.x - int(self.size / 2)

    @property
    def max_x(self):
        return self.center.x + int(self.size / 2)

    @property
    def min_y(self):
        return self.center.y - int(self.size / 2)

    @property
    def max_y(self):
        return self.center.y + int(self.size / 2)

    async def get_rooms(self):
        res = []
        from_x = max([self.min_x, map_repository.min_x])
        to_x = min([self.max_x, map_repository.max_x])
        for y in range(self.min_y, self.max_y):
            if map_repository.min_y <= y <= map_repository.max_y:
                data = await map_repository.get_rooms_on_y(y, from_x, to_x+1, self.center.z)

                if self.min_x <= map_repository.min_x:
                    data = ([None] * (self.size - len(data))) + data

                if self.max_x >= map_repository.max_x:
                    data = data + ([None] * (self.size - len(data)))

                res.extend(data)
                assert len(data) == 9, (len(data), from_x, to_x)
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
    a = Area(center=PosComponent([0, 0, 0]), square_size=size)
    loop = asyncio.get_event_loop()
    q = [(x and x.terrain.value or 0) for x in loop.run_until_complete(a.get_rooms())]
    p = ""
    c = {
        0: " ",
        1: "#",
        2: "."
    }
    lines = []
    for i in range(size, len(q), size):
        lines.append([c[x] for x in q[i-size:i]])
    ch = 0
    half = int((size*size)/2) + 1
    for i, line in enumerate(lines):
        x = ch + len(line)
        if x > half:
            lines[i][len(line) - (half-ch)] = 'X'
            break
        ch += len(line)

    for line in lines[::-1]:
        print("".join(line))

