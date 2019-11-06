import struct
import typing
from aioredis import Redis
from aioredis.commands import Pipeline

from core.src.world.room import Room


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

    def get_entity_position(self, entity_id: int):
        raise NotImplementedError

    def _coords_to_int(self, x: int, y: int) -> int:
        return x * self.mul + y

    def _int_to_coords(self, number: int) -> typing.Tuple[int, int]:
        x = int(number / self.mul)
        y = number % self.mul
        return x, y

    @staticmethod
    def _coords_to_hkey(x: int, y: int, z: int) -> str:
        return (struct.pack('H', x) + struct.pack('H', y) + struct.pack('H', z)).decode()

    def _set_room_data_on_bitmaps(self, room: Room):
        """
        Only z == 0 rooms.
        """
        assert not room.position.z
        p = self._get_pipeline()
        p.setrange(
            self.terrains_bitmap_key,
            self._coords_to_int(**room.position) * 8,
            struct.pack('B', room.terrain.value)
        )
        p.setrange(
            self.titles_ids_bitmap_bitmap_key,
            self._coords_to_int(**room.position) * 16,
            struct.pack('H', room.title_id)
        )
        p.setrange(
            self.descriptions_ids_bitmap_key,
            self._coords_to_int(**room.position) * 16,
            struct.pack('H', room.description_id)
        )

    def _set_room_data_on_hashmap(self, room: Room):
        """
        Only z != 0 rooms
        """
        assert room.position.z
        p = self._get_pipeline()
        hkey = self._coords_to_hkey(room.position.x, room.position.y, room.position.z)
        p.hset(
            self.z_valued_rooms_data_key, hkey,
            '{} {} {}'.format(room.title_id, room.description_id, room.terrain.value)
        )

    def _set_room_content(self, room: Room):
        p = self._get_pipeline()
        p.sadd(self.room_content_key, *room.entity_ids)

    async def set_room(self, room: Room, execute=True):
        if room.position.z:
            self._set_room_data_on_hashmap(room)
        else:
            self._set_room_data_on_bitmaps(room)
        self._set_room_content(room)
        execute and self._get_pipeline().execute()
        return room

    async def set_rooms(self, *rooms: Room):
        for room in rooms:
            self.set_room(room, execute=False)
        self._get_pipeline().execute()
        return rooms
