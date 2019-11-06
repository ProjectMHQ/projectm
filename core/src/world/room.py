import typing

from core.src.world.components import ComponentType
from core.src.world.types import TerrainEnum


class Room:
    def __init__(
        self,
        position=None,
        terrain=TerrainEnum.NULL,
        title_id=int,
        description_id=int,
        entity_ids=None
    ):
        self._position = position
        self._terrain = terrain
        self._title_id = title_id
        self._description_id = description_id
        self._entity_ids = entity_ids

    @property
    def position(self):
        return self._position

    @property
    def terrain(self):
        return self._terrain

    @property
    def title_id(self):
        return self._title_id

    @property
    def description_id(self):
        return self._description_id

    @property
    def entity_ids(self) -> typing.List[int]:
        return self._entity_ids
