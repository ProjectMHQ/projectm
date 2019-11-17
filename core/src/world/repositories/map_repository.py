import asyncio
import struct

from aioredis import Redis
from aioredis.commands import Pipeline

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

        self.max_y = 20  # FIXME TODO
        self.max_x = 58  # FIXME TODO
        self.min_x = 0
        self.min_y = 0

    async def redis(self) -> Redis:
        if not self._redis:
            self._redis = await self.redis_factory()
        return self._redis

    def _coords_to_int(self, x: int, y: int, bytesize=1) -> int:
        intcoord = (y * bytesize * self.mul) + x * bytesize
        return intcoord

    @staticmethod
    def _pack_coords(x: int, y: int, z: int) -> bytes:
        return struct.pack('>HHH', x, y, z)

    def _get_room_content(self, pipeline: Pipeline, x: int, y: int, z: int):
        pipeline.smembers(self.room_content_key.format(self._pack_coords(x, y, z)))

    def _get_rooms_content(self, pipeline: Pipeline, x: int, from_y: int, to_y: int, z: int):
        pipeline.sunion(
            *(self.room_content_key.format(c) for c in
            (self._pack_coords(x, y, z) for y in range(from_y, to_y)))
        )

    def _set_room_content(self, pipeline: Pipeline, room: Room):
        pipeline.sadd(self.room_content_key.format(
            self._pack_coords(room.position.x, room.position.y, room.position.z)
        ), *room.entity_ids)

    async def set_room(self, room: Room):
        return await self._set_room(room)

    async def _set_room(self, room: Room, external_pipeline=None):
        redis = await self.redis()
        pipeline = external_pipeline or redis.pipeline()
        if room.position.z:
            pipeline.hset(
                self.z_valued_rooms_data_key,
                self._pack_coords(room.position.x, room.position.y, room.position.z),
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

    async def get_room(self, position: RoomPosition) -> Room:
        redis = await self.redis()
        pipeline = redis.pipeline()
        if position.z:
            pipeline.hget(self.z_valued_rooms_data_key, self._pack_coords(
                position.x, position.y, position.z
            ))
        else:
            k = self._coords_to_int(position.x, position.y)
            pipeline.getrange(self.terrains_bitmap_key, k, k)
        self._get_room_content(pipeline, position.x, position.y, position.z)
        result = await pipeline.execute()
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

    async def get_rooms(self, *positions: RoomPosition):
        redis = await self.redis()
        pipeline = redis.pipeline()
        for position in positions:
            if position.z:
                pipeline.hget(self.z_valued_rooms_data_key, self._pack_coords(
                    position.x, position.y, position.z
                ))
            else:
                k = self._coords_to_int(position.x, position.y)
                pipeline.getrange(self.terrains_bitmap_key, k, k)
            self._get_room_content(
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
            content = [int(x) for x in result[i]]
            i += 1
            response.append(
                Room(
                    position=position,
                    terrain=TerrainEnum(terrain),
                    entity_ids=content
                )
            )
        return response

    async def get_rooms_on_y(self, y: int, from_x: int, to_x: int, z: int):
        assert to_x > from_x
        redis = await self.redis()
        pipeline = redis.pipeline()
        if z:
            packed_coordinates = (self._pack_coords(x, y, z) for x in range(from_x, to_x))
            pipeline.hmget(self.z_valued_rooms_data_key, *packed_coordinates)
        else:
            k = self._coords_to_int(from_x, y)
            pipeline.getrange(self.terrains_bitmap_key, k, k + ((to_x - from_x) - 1))
        _ = [self._get_room_content(pipeline, x, y, z) for x in range(from_x, to_x)]
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
                        entity_ids=[int(x) for x in result[d+1]]
                    )
                )
        return response
