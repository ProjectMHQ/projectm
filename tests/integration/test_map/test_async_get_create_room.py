import asyncio
import random
from collections import OrderedDict
from unittest import TestCase
import time

from core.src.world.services.system_utils import get_redis_factory, RedisType
from etc import settings
from core.src.world.repositories.map_repository import RedisMapRepository
from core.src.world.domain.room import Room, RoomPosition
from core.src.world.utils.world_types import TerrainEnum


class TestSetGetRooms(TestCase):
    def test(self):
        assert settings.INTEGRATION_TESTS
        assert settings.RUNNING_TESTS
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_test())

    async def async_test(self):
        sut = RedisMapRepository(get_redis_factory(RedisType.DATA))
        await (await sut.redis()).flushdb()
        futures = []
        d = {}
        i = 0
        max_x, max_y, max_z = 25, 25, 5
        sut.max_y = max_y
        sut.max_x = max_x
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
                                terrain=TerrainEnum.WALL_OF_BRICKS
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
                        [room.position.x, room.position.y, room.position.z],
                        [x, y, z]
                    )
        print('\n', i, ' rooms tested NO pipeline in {:.10f}'.format(time.time() - start))
        await (await sut.redis()).flushdb()
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
                    )
        await sut.set_rooms(*roomz.values())
        rooms = await sut.get_rooms(*positions)
        for i, room in enumerate(rooms):
            self.assertEqual(
                [
                    room.position.x, room.position.y, room.position.z,

                ],
                [
                    positions[i][0], positions[i][1], positions[i][2],
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
        sut = RedisMapRepository(get_redis_factory(RedisType.DATA))
        await (await sut.redis()).flushdb()
        max_x, max_y, max_z = 500, 500, 1
        sut.max_y = max_y
        sut.max_x = max_x
        start = time.time()
        i = 0
        print('\nBaking {}x{} map'.format(max_x, max_y))
        for x in range(max_x, -1, -1):
            roomz = OrderedDict()
            for y in range(max_y, -1, -1):
                for z in range(0, max_z):
                    i += 1
                    position = RoomPosition(x=x, y=y, z=z)
                    roomz['{}.{}.{}'.format(x, y, z)] = Room(
                        position=position,
                        terrain=random.choice([TerrainEnum.WALL_OF_BRICKS, TerrainEnum.PATH]),
                    )
            print(i, ' rooms saved')
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
        sut = RedisMapRepository(get_redis_factory(RedisType.DATA))
        await (await sut.redis()).flushdb()
        max_x, max_y = 50, 50
        sut.max_y = max_y
        sut.max_x = max_x
        start = time.time()
        print('\nBaking {}x{} map'.format(max_x, max_y))
        roomz = OrderedDict()
        for x in range(0, max_x):
            for y in range(0, max_y):
                position = RoomPosition(x=x, y=y, z=0)
                roomz['{}.{}.{}'.format(x, y, 0)] = Room(
                    position=position,
                    terrain=random.choice([TerrainEnum.WALL_OF_BRICKS, TerrainEnum.PATH]),
                    entity_ids=sorted([1, 2, 3, 4, y+5])
                )
        await sut.set_rooms(*roomz.values())
        print('\n{}x{} map baked in {}'.format(max_x, max_y, time.time() - start))

        from_x, to_x = 0, 9
        for yy in range(0, 210, 10):
            futures = [sut.get_rooms_on_y(0, from_x, to_x, 0) for _ in range(0, yy)]
            s = time.time()
            res = await asyncio.gather(*futures)
            print(
                'Get line of {} rooms. Concurrency: '.format(to_x-from_x), yy,
                ' users. Time: {:.8f}'.format(time.time() - s)
            )
            for r in res:
                for req in range(0, to_x):
                    k = '{}.{}.{}'.format(from_x + req, 0, 0)
                    self.assertEqual(
                        [
                            r[req].position.x, r[req].position.y, r[req].position.z, r[req].entity_ids],
                        [
                            roomz[k].position.x, roomz[k].position.y, roomz[k].position.z,
                            sorted(roomz[k].entity_ids)

                        ]
                    )
