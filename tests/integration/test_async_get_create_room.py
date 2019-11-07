import asyncio
import random
from collections import OrderedDict
from unittest import TestCase
import time
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
        start = time.time()
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
                    room = await sut.get_room(
                        RoomPosition(x, y, z)
                    )
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
        print('\n', i, ' rooms tested NO pipeline in {:.10f}'.format(time.time() - start))
        await redis.flushall(settings.REDIS_TEST_DB)
        _start = time.time()
        roomz = OrderedDict()
        positions = []
        for x in range(0, max_x):
            for y in range(0, max_y):
                for z in range(0, max_z):
                    position = RoomPosition(x=x, y=y, z=z)
                    positions.append(position)
                    roomz['{}.{}.{}'.format(x, y, z)] = Room(
                        position=position,
                        terrain=TerrainEnum.WALL_OF_BRICKS,
                        title_id=d['{}.{}.{}'.format(x, y, z)][0],
                        description_id=d['{}.{}.{}'.format(x, y, z)][1],
                    )
        await sut.set_rooms(*roomz.values())
        rooms = await sut.get_rooms(*positions)
        for i, room in enumerate(rooms):
            self.assertEqual(
                [
                    room.position.x, room.position.y, room.position.z,
                    room.title_id,
                    room.description_id

                ],
                [
                    positions[i][0], positions[i][1], positions[i][2],
                    roomz['{}.{}.{}'.format(room.position.x, room.position.y, room.position.z)].title_id,
                    roomz['{}.{}.{}'.format(room.position.x, room.position.y, room.position.z)].description_id,
                ]
            )
        print('\n', i+1, ' rooms tested WITH pipeline in {:.10f}'.format(time.time() - _start))

        positions = []
        i = 0
        for x in range(0, 9):
            for y in range(0, 9):
                positions.append(RoomPosition(x, y, 0))
                i += 1
        print('\n Starting benchmarks: \n')
        for x in range(1, 110, 10):
            futures = [sut.get_rooms(*positions) for _ in range(0, x)]
            s = time.time()
            await asyncio.gather(*futures)
            print(
                'Rooms: ', i, '. Concurrency: ', x,
                ' users. Time: {:.8f}'.format(time.time() - s)
            )

        positions = []
        i = 0
        for x in range(0, 9):
            y = 1
            positions.append(RoomPosition(x, y, 0))
            i += 1

        for x in range(1, 110, 10):
            futures = [sut.get_rooms(*positions) for _ in range(0, x)]
            s = time.time()
            await asyncio.gather(*futures)
            print(
                'Rooms: ', i, '. Concurrency: ', x,
                ' users. Time: {:.8f}'.format(time.time() - s)
            )


class TestBigMap(TestCase):
    def test(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.asyncio_test())

    async def asyncio_test(self):
        redis = await redis_pool()
        await redis.flushdb(settings.REDIS_TEST_DB)
        sut = MapRepository(redis)
        max_x, max_y, max_z = 500, 500, 1
        start = time.time()
        print('\nBaking {}x{} map'.format(max_x, max_y))
        for x in range(0, max_x):
            roomz = OrderedDict()
            for y in range(0, max_y):
                for z in range(0, max_z):
                    position = RoomPosition(x=x, y=y, z=z)
                    roomz['{}.{}.{}'.format(x, y, z)] = Room(
                        position=position,
                        terrain=random.choice([TerrainEnum.WALL_OF_BRICKS, TerrainEnum.PATH]),
                        title_id=1,
                        description_id=1,
                    )
            print(500 * x, ' rooms saved')
            await sut.set_rooms(*roomz.values())
        print('\n{}x{} map baked in {}'.format(max_x, max_y, time.time() - start))
        start = time.time()
        print('\nFetching {}x{} map'.format(max_x, max_y))
        tot = 0
        for x in range(0, max_x):
            res = await sut.get_rooms(*(RoomPosition(x, y, 0) for y in range(0, max_y)))
            tot += len(res)
        print('\n{}x{} map fetched in {} - total: {}'.format(max_x, max_y, time.time() - start, tot))


class TestMapLines(TestCase):
    def test(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.asyncio_test())

    async def asyncio_test(self):
        redis = await redis_pool()
        sut = MapRepository(redis)
        await redis.flushdb(settings.REDIS_TEST_DB)
        max_x, max_y, max_z = 50, 50, 1
        start = time.time()
        print('\nBaking {}x{} map'.format(max_x, max_y))
        roomz = OrderedDict()
        for x in range(0, max_x):
            for y in range(0, max_y):
                for z in range(0, max_z):
                    position = RoomPosition(x=x, y=y, z=z)
                    roomz['{}.{}.{}'.format(x, y, z)] = Room(
                        position=position,
                        terrain=random.choice([TerrainEnum.WALL_OF_BRICKS, TerrainEnum.PATH]),
                        title_id=x+3,
                        description_id=y+3,
                        entity_ids=sorted([1, 2, 3, 4, y+5])
                    )
        await sut.set_rooms(*roomz.values())
        print('\n{}x{} map baked in {}'.format(max_x, max_y, time.time() - start))

        from_y, to_y = 0, 9
        for x in range(1, 210, 10):
            futures = [sut.get_rooms_on_y(0, from_y, to_y, 0) for _ in range(0, x)]
            s = time.time()
            res = await asyncio.gather(*futures)
            print(
                'Get line of {} rooms. Concurrency: '.format(to_y-from_y), x,
                ' users. Time: {:.8f}'.format(time.time() - s)
            )
            for r in res:
                for req in range(0, to_y):
                    k = '{}.{}.{}'.format(0, from_y + req, 0)
                    self.assertEqual(
                        [
                            r[req].position.x, r[req].position.y, r[req].position.z,
                            r[req].title_id, r[req].description_id, r[req].entity_ids],
                        [
                            roomz[k].position.x, roomz[k].position.y, roomz[k].position.z,
                            roomz[k].title_id, roomz[k].description_id, sorted(roomz[k].entity_ids)

                        ]
                    )
        print('Rooms: %s' '\n'.join([str(x) for x in r]))
