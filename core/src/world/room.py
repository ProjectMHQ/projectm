import typing

from core.src.world.types import TerrainEnum


RoomPosition = typing.NamedTuple(
    'RoomPosition', (
        ('x', int),
        ('y', int),
        ('z', int)
    )
)


class Room:
    def __init__(
        self,
        position: RoomPosition = None,
        terrain: TerrainEnum = TerrainEnum.NULL,
        title_id: int = 0,
        description_id: int = 0,
        entity_ids: typing.List[int] = list()
    ):
        self._position = position
        self._terrain = terrain
        self._title_id = title_id
        self._description_id = description_id
        self._entity_ids = entity_ids

    @property
    def position(self) -> RoomPosition:
        return self._position

    @property
    def terrain(self) -> TerrainEnum:
        return self._terrain

    @property
    def title_id(self) -> int:
        return self._title_id

    @property
    def description_id(self) -> int:
        return self._description_id

    @property
    def entity_ids(self) -> typing.List[int]:
        return self._entity_ids
