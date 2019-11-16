import asyncio

from core.src.world.builder import map_repository
from core.src.world.domain.room import Room, RoomPosition
from core.src.world.world_types import TerrainEnum

terrains = {
    "#": TerrainEnum.WALL_OF_BRICKS,
    ".": TerrainEnum.PATH,
    "~": TerrainEnum.GRASS,
    " ": None
}


def parse(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    lines = [l.strip() for l in lines]
    max_y = len(lines) - 1
    max_x = max([len(line) for line in lines]) - 1
    rooms = []
    for x in range(0, max_x):
        for y in range(0, max_y):
            try:
                room_enum = terrains[lines[x][y]]
                if room_enum:
                    rooms.append(
                        Room(
                            position=RoomPosition(x=x, y=y, z=0),
                            terrain=room_enum
                        )
                    )
            except IndexError:
                pass
    return rooms


async def set_rooms(data):
    res = await map_repository.set_rooms(*data)
    print('\n'.join([str(x) for x in res]))


content = parse('./mappa_prova_1')
asyncio.get_event_loop().run_until_complete(set_rooms(content))
