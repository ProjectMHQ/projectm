import asyncio
import random
from unittest import TestCase
from etc import settings
from core.src.world.builder import redis_pool
from core.src.world.repositories.map_repository import MapRepository
from core.src.world.room import Room, RoomPosition
from core.src.world.types import TerrainEnum


class TestSetGetRooms(TestCase):
    def test(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_test())

    async def async_test(self):
        redis = await redis_pool()
        await redis.flushdb(settings.REDIS_TEST_DB)
        sut = MapRepository(redis)
        futures = []
        d = {}
        i = 0
        max_x, max_y, max_z = 25, 25, 5
        for x in range(0, max_x):
            for y in range(0, max_y):
                for z in range(0, max_z):
                    i += 1
                    d['{}.{}.{}'.format(x, y, z)] = [random.randint(0, 65530), random.randint(0, 65530)]
                    futures.append(
                        sut.set_room(
                            Room(
                                position=RoomPosition(x=x, y=y, z=z),
                                terrain=TerrainEnum.WALL_OF_BRICKS,
                                title_id=d['{}.{}.{}'.format(x, y, z)][0],
                                description_id=d['{}.{}.{}'.format(x, y, z)][1],
                            )
                        )
                    )
        await asyncio.gather(*futures)
        for x in range(0, max_x):
            for y in range(0, max_y):
                for z in range(0, max_z):
                    room = await sut.get_room(x, y, z)
                    self.assertEqual(
                        [
                            room.position.x, room.position.y, room.position.z,
                            room.title_id,
                            room.description_id

                        ],
                        [
                            x, y, z,
                            d['{}.{}.{}'.format(x, y, z)][0],
                            d['{}.{}.{}'.format(x, y, z)][1],
                        ]
                    )
        print(i, ' rooms tested')
