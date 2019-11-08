import asyncio
import struct

from aioredis import Redis
from aioredis.commands import Pipeline

from core.src.world.domain.room import Room, RoomPosition
from core.src.world.types import TerrainEnum


class RedisMapRepository:
    def __init__(self, redis_factory: callable):
        self.redis_factory = redis_factory
        self.prefix = 'm'
        self.terrains_suffix = 'ter'
        self.descriptions_ids_suffix = 'des'
        self.titles_ids_suffix = 'tit'
        self.z_valued_rooms_data_suffix = 'd'
        self.room_content_suffix = 'c'

        self.terrains_bitmap_key = '{}:{}'.format(self.prefix, self.terrains_suffix)
        self.descriptions_ids_bitmap_key = '{}:{}'.format(self.prefix, self.descriptions_ids_suffix)
        self.titles_ids_bitmap_bitmap_key = '{}:{}'.format(self.prefix, self.titles_ids_suffix)
        self.room_content_key = '{}:{}:{}'.format(self.prefix, '{}', self.room_content_suffix)
        self.z_valued_rooms_data_key = '{}:{}'.format(self.prefix, self.z_valued_rooms_data_suffix)
        self.mul = 10**4
        self._pipelines = None
        self._redis = None

    async def redis(self) -> Redis:
        if not self._redis:
            self._redis = await self.redis_factory()
        return self._redis

    def _coords_to_int(self, x: int, y: int, bytesize=2) -> int:
        return x * bytesize * self.mul + y * bytesize

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
                '{} {} {}'.format(room.terrain.value, room.title_id, room.description_id)
            )
        else:
            num = self._coords_to_int(room.position.x, room.position.y)
            pipeline.setrange(
                self.terrains_bitmap_key, num, struct.pack('>H', room.terrain.value)
            )
            pipeline.setrange(
                self.titles_ids_bitmap_bitmap_key, num, struct.pack('>H', room.title_id)
            )

            pipeline.setrange(
                self.descriptions_ids_bitmap_key, num, struct.pack('>H', room.description_id)
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
            pipeline.getrange(self.terrains_bitmap_key, k, k + 1)
            pipeline.getrange(self.titles_ids_bitmap_bitmap_key, k, k + 1)
            pipeline.getrange(self.descriptions_ids_bitmap_key, k, k + 1)
        self._get_room_content(pipeline, position.x, position.y, position.z)
        result = await pipeline.execute()
        if position.z:
            terrain, title_id, description_id = [int(x) for x in result[0].split(b' ')]
            content = [int(x) for x in result[1]]
        else:
            terrain, title_id, description_id = struct.unpack('>HHH', result[0]+result[1]+result[2])
            content = [int(x) for x in result[3]]

        return Room(
            position=position,
            terrain=TerrainEnum(terrain),
            title_id=title_id,
            description_id=description_id,
            entity_ids=content
        )

    async def set_rooms(self, *rooms: Room):
        redis = await self.redis()
        pipeline = redis.pipeline()
        await asyncio.gather(*(self._set_room(room, external_pipeline=pipeline) for room in rooms))
        await pipeline.execute()

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
                pipeline.getrange(self.terrains_bitmap_key, k, k + 1)
                pipeline.getrange(self.titles_ids_bitmap_bitmap_key, k, k + 1)
                pipeline.getrange(self.descriptions_ids_bitmap_key, k, k + 1)

            self._get_room_content(
                pipeline, position.x, position.y, position.z
            )
        result = await pipeline.execute()
        i = 0
        response = []
        for position in positions:
            if position.z:
                terrain, title_id, description_id = [int(x) for x in result[i].split(b' ')]
                i += 1
            else:
                terrain, title_id, description_id = struct.unpack('>HHH', result[i]+result[i+1]+result[i+2])
                i += 3
            content = [int(x) for x in result[i]]
            i += 1
            response.append(
                Room(
                    position=position,
                    terrain=TerrainEnum(terrain),
                    title_id=title_id,
                    description_id=description_id,
                    entity_ids=content
                )
            )
        return response

    async def get_rooms_on_y(self, x: int, from_y: int, to_y: int, z: int):
        assert to_y > from_y
        redis = await self.redis()
        pipeline = redis.pipeline()
        if z:
            packed_coordinates = (self._pack_coords(x, y, z) for y in range(from_y, to_y))
            pipeline.hmget(self.z_valued_rooms_data_key, *packed_coordinates)
        else:
            k = self._coords_to_int(x, from_y)
            pipeline.getrange(self.terrains_bitmap_key, k, k + ((to_y - from_y) * 2 - 1))
            pipeline.getrange(self.titles_ids_bitmap_bitmap_key, k, k + ((to_y - from_y) * 2 - 1))
            pipeline.getrange(self.descriptions_ids_bitmap_key, k, k + ((to_y - from_y) * 2 - 1))

        _ = [self._get_room_content(pipeline, x, y, z) for y in range(from_y, to_y)]
        response = []
        i = 0
        result = await pipeline.execute()
        if z:
            res = result[0]
            d = 0
            for key, value in res[0].items():
                terrain, title_id, description_id = [int(x) for x in value.split(b' ')]
                response.append(
                    Room(
                        position=RoomPosition(x, from_y + d, z),
                        terrain=TerrainEnum(terrain),
                        title_id=title_id,
                        description_id=description_id
                    )
                )
                d += 1
            for res in result[i+1]:
                response[i].add_entity_ids(list(res))
        else:
            terrains = struct.unpack('>' + 'H'*(to_y - from_y), result[0])
            title_ids = struct.unpack('>' + 'H' * (to_y - from_y), result[1])
            description_ids = struct.unpack('>' + 'H' * (to_y - from_y), result[2])
            for d in range(0, to_y-from_y):
                response.append(
                    Room(
                        position=RoomPosition(x, from_y + d, z),
                        terrain=TerrainEnum(terrains[d]),
                        title_id=title_ids[d],
                        description_id=description_ids[d],
                        entity_ids=[int(x) for x in result[3+d]]
                    )
                )
        return response
