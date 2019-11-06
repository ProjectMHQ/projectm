import asyncio
import struct
import typing
from aioredis import Redis
from aioredis.commands import Pipeline

from core.src.world.room import Room, RoomPosition
from core.src.world.types import TerrainEnum


class MapRepository:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.prefix = 'm'
        self.terrains_suffix = 'te'
        self.descriptions_ids_suffix = 'd'
        self.titles_ids_suffix = 'ti'
        self.z_valued_rooms_data_suffix = 'd'
        self.room_content_suffix = 'c'

        self.terrains_bitmap_key = '{}:{}'.format(self.prefix, self.terrains_suffix)
        self.descriptions_ids_bitmap_key = '{}:{}'.format(self.prefix, self.descriptions_ids_suffix)
        self.titles_ids_bitmap_bitmap_key = '{}:{}'.format(self.prefix, self.titles_ids_suffix)
        self.room_content_key = '{}:{}:{}'.format(self.prefix, '{}', self.room_content_suffix)
        self.z_valued_rooms_data_key = '{}:{}'.format(self.prefix, self.z_valued_rooms_data_key)
        self.mul = 10**4
        self._pipeline = None

    def _get_pipeline(self) -> Pipeline:
        if not self._pipeline:
            self._pipeline = self.redis.pipeline()
        return self._pipeline

    async def _execute_pipeline(self):
        """
        DO NOT use pipeline.execute(), use this method instead.
        """
        res = await self._pipeline.execute()
        self._pipeline = None
        return res

    def _coords_to_int(self, x: int, y: int) -> int:
        return x * self.mul + y

    def _int_to_coords(self, number: int) -> typing.Tuple[int, int]:
        x = int(number / self.mul)
        y = number % self.mul
        return x, y

    @staticmethod
    def _pack_coords(x: int, y: int, z: int) -> bytes:
        return struct.pack('HHH', x, y, z)

    def _set_room_data_on_bitmaps(self, room: Room):
        """
        Only z == 0 rooms.
        """
        assert not room.position.z
        p = self._get_pipeline()
        num = self._coords_to_int(**room.position)
        p.setrange(
            self.terrains_bitmap_key, num * 8, struct.pack('B', room.terrain.value)
        )
        p.setrange(
            self.titles_ids_bitmap_bitmap_key, num * 16, struct.pack('H', room.title_id)
        )
        p.setrange(
            self.descriptions_ids_bitmap_key, num * 16, struct.pack('H', room.description_id)
        )

    def _set_room_data_on_hashmap(self, room: Room):
        """
        Only z != 0 rooms
        """
        assert room.position.z
        p = self._get_pipeline()
        hkey = self._pack_coords(room.position.x, room.position.y, room.position.z)
        p.hset(
            self.z_valued_rooms_data_key, hkey,
            '{} {} {}'.format(room.terrain.value, room.title_id, room.description_id)
        )

    def _set_room_content(self, room: Room):
        p = self._get_pipeline()
        p.sadd(self.room_content_key.format(
            self._pack_coords(room.position.x, room.position.y, room.position.z)
        ), *room.entity_ids)

    async def _set_room(self, room: Room, execute=True):
        if room.position.z:
            self._set_room_data_on_hashmap(room)
        else:
            self._set_room_data_on_bitmaps(room)
        self._set_room_content(room)
        execute and self._get_pipeline().execute()
        return room
    
    def _get_rooms_data_from_hashmap(self, x: int, y: int, z: int):
        assert z
        p = self._get_pipeline()
        p.hget(self.z_valued_rooms_data_key, self._pack_coords(x, y, z))
    
    def _get_rooms_data_from_bitmaps(self, x: int, y: int):
        p = self._get_pipeline()
        p.getrange(
            self.terrains_bitmap_key, self._coords_to_int(x, y) * 8
        )
        p.getrange(
            self.titles_ids_bitmap_bitmap_key, self._coords_to_int(x, y) * 16
        )
        p.getrange(
            self.descriptions_ids_bitmap_key, self._coords_to_int(x, y) * 16
        )
    
    def _get_rooms_content(self, x: int, y: int, z: int):
        p = self._get_pipeline()
        p.smembers(self.room_content_key.format(self._pack_coords(x, y, z)))

    async def set_room(self, room: Room):
        return await self._set_room(room, execute=True)

    async def set_rooms(self, *rooms: Room):
        await asyncio.gather(
            *(self._set_room(room, execute=False) for room in rooms)
        )
        self._get_pipeline().execute()
        return rooms

    async def get_room(self, x: int, y: int, z: int) -> Room:
        pipeline = self._get_pipeline()
        self._get_rooms_data_from_hashmap(x, y, z) if z else self._get_rooms_data_from_bitmaps(x, y)
        self._get_rooms_content(x, y, z)
        result = await pipeline.execute()
        if not z:
            room_data = struct.unpack('HHH', result[0]+result[1]+result[2])
            content = [int(x) for x in result[3]]
        else:
            room_data = (int(x) for x in result[0].split(' '))
            content = [int(x) for x in result[1]]
        return Room(
            position=RoomPosition(x=x, y=y, z=z),
            terrain=TerrainEnum(room_data[0]),
            title_id=room_data[1],
            description_id=room_data[2],
            entity_ids=content
        )
