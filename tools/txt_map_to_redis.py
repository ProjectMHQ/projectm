import sys

from core.src.world.components import PosComponent

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
                        position=PosComponent([x, max_y-y, 0]),
                        terrain=room_enum
                    )
                )
    return rooms


async def set_rooms(data):
    await map_repository.set_rooms(*data)


def parse(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    return lines


if __name__ == '__main__':

    lines = parse('./tools/mappa_prova_1')
    content = parse_lines(lines)

    asyncio.get_event_loop().run_until_complete(set_rooms(content))
