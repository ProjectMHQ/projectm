import asyncio
import struct

from aioredis import Redis
from aioredis.commands import Pipeline

from core.src.world.room import Room, RoomPosition
from core.src.world.types import TerrainEnum


class MapRepository:
    def __init__(self, redis: Redis):
        self.redis = redis
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

    async def _execute_pipeline(self):
        """
        DO NOT use pipeline.execute(), use this method instead.
        """
        res = await self._pipeline.execute()
        self._pipeline = None
        return res

    def _coords_to_int(self, x: int, y: int, bytesize=2) -> int:
        return x * bytesize * self.mul + y * bytesize

    @staticmethod
    def _pack_coords(x: int, y: int, z: int) -> bytes:
        return struct.pack('>HHH', x, y, z)

    def _get_room_content(self, pipeline: Pipeline, x: int, y: int, z: int):
        pipeline.smembers(self.room_content_key.format(self._pack_coords(x, y, z)))

    def _set_room_content(self, pipeline: Pipeline, room: Room):
        pipeline.sadd(self.room_content_key.format(
            self._pack_coords(room.position.x, room.position.y, room.position.z)
        ), *room.entity_ids)

    async def set_room(self, room: Room):
        return await self._set_room(room)

    async def _set_room(self, room: Room, external_pipeline=None):
        pipeline = external_pipeline or self.redis.pipeline()
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
        pipeline = self.redis.pipeline()
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
        pipeline = self.redis.pipeline()
        await asyncio.gather(*(self._set_room(room, external_pipeline=pipeline) for room in rooms))
        await pipeline.execute()

    async def get_rooms(self, *positions: RoomPosition):
        pipeline = self.redis.pipeline()
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
        #s = time.time()
        result = await pipeline.execute()
        #print('pipeline executed in {:.15f}'.format(time.time() - s))
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
