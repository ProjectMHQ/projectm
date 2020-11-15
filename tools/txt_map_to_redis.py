import sys

from core.src.world.components.position import PositionComponent
from core.src.world.services.system_utils import connection_pools

sys.path.insert(0, './')

import asyncio

from core.src.world.builder import map_repository
from core.src.world.domain.room import Room
from core.src.world.utils.world_types import TerrainEnum

terrains = {
    "#": TerrainEnum.WALL_OF_BRICKS,
    ".": TerrainEnum.PATH,
    "~": TerrainEnum.GRASS,
    " ": None
}

done = 0


def parse_lines(lines):
    lines = [l.strip() for l in lines]
    max_y = len(lines) - 1
    max_x = max([len(line) for line in lines]) - 1
    rooms = []
    for y in range(max_y, -1, -1):
        for x in range(0, max_x + 1):
            room_enum = terrains[lines[y][x]]
            if room_enum:
                rooms.append(
                    Room(
                        position=PositionComponent().set_list_coordinates([x, max_y-y, 0]),
                        terrain=room_enum
                    )
                )
    return rooms


def parse(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    return lines


async def set_rooms(c):
    await map_repository.set_rooms(*c)
    for key, pool in connection_pools.items():
        pool.close()


if __name__ == '__main__':
    lines = parse('./tools/mappa_prova_1')
    content = parse_lines(lines)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_rooms(content))
