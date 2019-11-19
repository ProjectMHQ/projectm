import typing

from core.src.world.utils.world_types import TerrainEnum, is_terrain_walkable

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
        entity_ids: typing.List[int] = list()
    ):
        self._position = position
        self._terrain = terrain
        self._entity_ids = entity_ids

    @property
    def position(self) -> RoomPosition:
        return self._position

    @property
    def terrain(self) -> TerrainEnum:
        return self._terrain

    @property
    def entity_ids(self) -> typing.List[int]:
        return self._entity_ids

    def add_entity_ids(self, *data: int):
        self.entity_ids.extend([x for x in data])

    """
    I still have to handle title, description, etc... 
    this is a placeholder for testing
    """
    @property
    def description(self) -> str:
        return "Room Description"  # FIXME TODO

    @property
    def title(self) -> str:
        return "Room Title"  # FIXME TODO

    @property
    def content(self) -> typing.List[str]:
        if self.position.x == 1 and self.position.y == 1 and not self.position.z:
            # FIXME REMOVE TODO
            return ['A three-headed monkey']
        return []

    def __str__(self):
        return '''
        position: %s,
        terrain: %s,
        title: %s,
        description: %s,
        entity_ids: %s
        ''' % (
            self.position and 'x: %s, y: %s, z: %s' % (
                self.position.x, self.position.y, self.position.z
            ) or '',
            self.terrain and self.terrain.name,
            self.title,
            self.description,
            self.entity_ids or []
        )

    async def walkable_by(self, entity):
        return is_terrain_walkable(self.terrain)
