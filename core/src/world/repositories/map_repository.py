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

    def _coords_to_int(self, x: int, y: int) -> int:
        return x * 2 * self.mul + y * 2

    @staticmethod
    def _pack_coords(x: int, y: int, z: int) -> bytes:
        return struct.pack('>HHH', x, y, z)

    def _set_room_content(self, pipeline: Pipeline, room: Room):
        pipeline.sadd(self.room_content_key.format(
            self._pack_coords(room.position.x, room.position.y, room.position.z)
        ), *room.entity_ids)

    async def set_room(self, room: Room):
        pipeline = self.redis.pipeline()
        if room.position.z:
            hkey = self._pack_coords(room.position.x, room.position.y, room.position.z)
            pipeline.hset(
                self.z_valued_rooms_data_key, hkey,
                '{} {} {}'.format(room.terrain.value, room.title_id, room.description_id)
            )
        else:
            num = self._coords_to_int(room.position.x, room.position.y)
            pipeline.setrange(
                self.terrains_bitmap_key, num, struct.pack('>B', room.terrain.value)
            )
            pipeline.setrange(
                self.titles_ids_bitmap_bitmap_key, num, struct.pack('>H', room.title_id)
            )
            try:
                pipeline.setrange(
                    self.descriptions_ids_bitmap_key, num, struct.pack('>H', room.description_id)
                )
            except:
                raise
        any(room.entity_ids) and self._set_room_content(pipeline, room)
        await pipeline.execute()
        return room

    def _get_rooms_content(self, pipeline: Pipeline, x: int, y: int, z: int):
        pipeline.smembers(self.room_content_key.format(self._pack_coords(x, y, z)))

    async def get_room(self, x: int, y: int, z: int) -> Room:
        pipeline = self.redis.pipeline()
        if z:
            pipeline.hget(self.z_valued_rooms_data_key, self._pack_coords(x, y, z))
        else:
            k = self._coords_to_int(x, y)
            pipeline.getrange(self.terrains_bitmap_key, k, k)
            pipeline.getrange(self.titles_ids_bitmap_bitmap_key, k, k + 1)
            pipeline.getrange(self.descriptions_ids_bitmap_key, k, k + 1)
        self._get_rooms_content(pipeline, x, y, z)
        result = await pipeline.execute()
        if z:
            terrain, title_id, description_id = result[0] and [int(x) for x in result[0].split(b' ')] or [0, 0, 0]
            content = [int(x) for x in result[1]]
        else:
            terrain, = struct.unpack('>B', result[0])
            title_id, description_id = struct.unpack('>HH', result[1]+result[2])
            content = [int(x) for x in result[3]]

        return Room(
            position=RoomPosition(x=x, y=y, z=z),
            terrain=TerrainEnum(terrain),
            title_id=title_id,
            description_id=description_id,
            entity_ids=content
        )
