import asyncio
import binascii
import os
import struct

import typing

import aioredis
from core.src.auth.logging_factory import LOGGER
from core.src.world import exceptions
from core.src.world.components.pos import PosComponent
from core.src.world.domain.room import Room, RoomPosition
from core.src.world.utils.world_types import TerrainEnum


class RedisMapRepository:
    def __init__(self, redis_factory: callable):
        self.redis_factory = redis_factory
        self.prefix = 'm'
        self.terrains_suffix = 't'
        self.z_valued_rooms_data_suffix = 'd'
        self.room_content_suffix = 'c'

        self.terrains_bitmap_key = '{}:{}'.format(self.prefix, self.terrains_suffix)
        self.room_content_key = '{}:{}:{}'.format(self.prefix, '{}', self.room_content_suffix)
        self.z_valued_rooms_data_key = '{}:{}'.format(self.prefix, self.z_valued_rooms_data_suffix)
        self.mul = 10**4
        self._pipelines = None
        self._redis = None

        self.max_y = 67  # FIXME TODO
        self.max_x = 131      # FIXME TODO
        self.min_x = 0
        self.min_y = 0
        self.async_lock = asyncio.Lock()

    def get_room_key(self, x, y, z):
        if z:
            return self.room_content_key.format('{}.{}.{}'.format(x, y, z))
        else:
            return self.room_content_key.format('{}.{}'.format(x, y))

    async def redis(self) -> aioredis.Redis:
        await self.async_lock.acquire()
        try:
            if not self._redis:
                self._redis = await self.redis_factory()
        finally:
            self.async_lock.release()
        return self._redis

    def _coords_to_int(self, x: int, y: int, bytesize=1) -> int:
        intcoord = (y * bytesize * self.mul) + x * bytesize
        return intcoord

    @staticmethod
    def _pack_coords(x: int, y: int, z: int) -> bytes:
        return struct.pack('>hhh', x, y, z)

    def _get_room_content(self, pipeline, x: int, y: int, z: int):
        pipeline.zrange(self.get_room_key(x, y, z))

    def _get_rooms_content(self, pipeline, x: int, from_y: int, to_y: int, z: int):
        key = 'temp:rmc:{}'.format(binascii.unhexlify(os.urandom(8)).decode())
        pipeline.zunionstore(
            key, *(self.get_room_key(*c) for c in ((x, y, z) for y in range(from_y, to_y)))
        )
        pipeline.zrange(key)
        pipeline.delete(key)

    def _set_room_content(self, pipeline, room: Room):
        res = []
        for x in room.entity_ids:
            res.extend([0, x])
        pipeline.zadd(self.get_room_key(room.position.x, room.position.y, room.position.z), *res)

    async def set_room(self, room: Room):
        return await self._set_room(room)

    async def _set_room(self, room: Room, external_pipeline=None):
        redis = await self.redis()
        pipeline = external_pipeline or redis.pipeline()
        if room.position.z:
            pipeline.hset(
                self.z_valued_rooms_data_key,
                '{}.{}.{}'.format(room.position.x, room.position.y, room.position.z),
                '{}'.format(room.terrain.value)
            )
        else:
            num = self._coords_to_int(room.position.x, room.position.y)
            pipeline.setrange(
                self.terrains_bitmap_key, num, struct.pack('B', room.terrain.value)
            )
        any(room.entity_ids) and self._set_room_content(pipeline, room)
        not external_pipeline and await pipeline.execute()
        return room

    async def get_room(self, position: RoomPosition) -> typing.Optional[Room]:
        if (self.min_y > position.y) or (self.max_y < position.y):
            raise exceptions.RoomError
        if (self.min_x > position.x) or (self.max_x < position.x):
            raise exceptions.RoomError

        redis = await self.redis()
        pipeline = redis.pipeline()
        if position.z:
            pipeline.hget(
                self.z_valued_rooms_data_key,
                '{}.{}.{}'.format(position.x, position.y, position.z),
            )
        else:
            k = self._coords_to_int(position.x, position.y)
            pipeline.getrange(self.terrains_bitmap_key, k, k)
        self._get_room_content(pipeline, position.x, position.y, position.z)
        result = await pipeline.execute()
        if not result or not result[0]:
            LOGGER.core.error('Room Error. Request: %s, Result: %s', position, result)
            raise exceptions.RoomError
        if position.z:
            terrain = int(result[0])
        else:
            terrain = int(struct.unpack('B', result[0])[0])
        content = [int(x) for x in result[1]]

        return Room(
            position=position,
            terrain=TerrainEnum(terrain),
            entity_ids=content
        )

    async def set_rooms(self, *rooms: Room):
        redis = await self.redis()
        pipeline = redis.pipeline()
        response = await asyncio.gather(*(self._set_room(room, external_pipeline=pipeline) for room in rooms))
        await pipeline.execute()
        return response

    async def get_rooms(self, *positions: RoomPosition, get_content=True):
        redis = await self.redis()
        pipeline = redis.pipeline()
        for position in positions:
            if position.z:
                pipeline.hget(
                    self.z_valued_rooms_data_key,
                    '{}.{}.{}'.format(position.x, position.y, position.z)
                )
            else:
                k = self._coords_to_int(position.x, position.y)
                pipeline.getrange(self.terrains_bitmap_key, k, k)
            get_content and self._get_room_content(
                pipeline, position.x, position.y, position.z
            )
        result = await pipeline.execute()
        i = 0
        response = []
        for position in positions:
            if position.z:
                terrain = int(result[i])
            else:
                terrain = int(struct.unpack('B', result[i])[0])
            i += 1
            if get_content:
                content = [int(x) for x in result[i]]
                i += 1
            else:
                content = []
            response.append(
                Room(
                    position=position,
                    terrain=TerrainEnum(terrain),
                    entity_ids=content
                )
            )
        return response

    async def get_rooms_on_y(self, y: int, from_x: int, to_x: int, z: int, get_content=True):
        assert to_x > from_x
        redis = await self.redis()
        pipeline = redis.pipeline()
        if z:
            packed_coordinates = (self._pack_coords(x, y, z) for x in range(from_x, to_x))
            pipeline.hmget(self.z_valued_rooms_data_key, *packed_coordinates)
        else:
            k = self._coords_to_int(from_x, y)
            pipeline.getrange(self.terrains_bitmap_key, k, k + ((to_x - from_x) - 1))
        get_content and [self._get_room_content(pipeline, x, y, z) for x in range(from_x, to_x)]
        response = []
        i = 0
        result = await pipeline.execute()
        if z:
            res = result[0]
            d = 0
            for key, value in res[0].items():
                terrain = int(value)
                response.append(
                    Room(
                        position=RoomPosition(from_x + d, y, z),
                        terrain=TerrainEnum(terrain),
                    )
                )
                d += 1
            for res in result[i+1]:
                response[i].add_entity_ids(list(res))
        else:
            terrains = struct.unpack('B' * (to_x - from_x), result[0])
            for d in range(0, to_x - from_x):
                response.append(
                    Room(
                        position=RoomPosition(from_x + d, y, z),
                        terrain=TerrainEnum(terrains[d]),
                        entity_ids=get_content and [int(x) for x in result[d+1]] or []
                    )
                )
        return response

    async def remove_entity_from_map(self, entity_id: int, position: PosComponent, pipeline=None):
        if not pipeline:
            redis = await self.redis()
            pipeline = redis.pipeline()
        pipeline.zrem(self.get_room_key(position.x, position.y, position.z), '{}'.format(entity_id))
        pipeline.hdel('positions', entity_id)
        if not pipeline:
            res = await pipeline.execute()
            return bool(res[1])

    def update_map_position_for_entity(self, position: PosComponent, entity, pipeline):
        if position.previous_position:
            prev_set_name = self.get_room_key(
                position.previous_position.x,
                position.previous_position.y,
                position.previous_position.z
            )
            pipeline.zrem(prev_set_name, '{}'.format(entity.entity_id))
        if position.value:
            new_set_name = self.get_room_key(position.x, position.y, position.z)
            pipeline.zadd(new_set_name, 0, '{}'.format(entity.entity_id))
            pipeline.hset('positions', entity.entity_id, [position.x, position.y, position.z])

    async def get_all_entity_ids_in_area(self, area):
        redis = await self.redis()
        pipeline = redis.pipeline()
        key = binascii.hexlify(os.urandom(8)).decode()
        pipeline.zunionstore(
            'temp:{}'.format(key), *(
                self.get_room_key(r[0], r[1], r[2]) for r in area.make_coordinates().rooms_and_peripherals_coordinates
            )
        )
        pipeline.zrange('temp:{}'.format(key), 0, -1)
        pipeline.delete('temp:{}'.format(key))
        result = await pipeline.execute()
        return result[1]

    async def get_positions_for_entity_ids(self, *entity_ids: int):
        redis = await self.redis()
        return await redis.hmget('positions', *entity_ids)
