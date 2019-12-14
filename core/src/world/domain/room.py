import typing

from core.src.world.entity import Entity
from core.src.world.utils.world_types import TerrainEnum, is_terrain_walkable, EvaluatedEntity

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
        self._content: typing.Set[EvaluatedEntity] = set()

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
    def content(self) -> typing.List[EvaluatedEntity]:
        return list(self._content)

    @property
    def has_entities(self):
        return bool(self._entity_ids)

    @property
    def json_content(self) -> typing.List[typing.Dict]:
        res = []
        for e in self.content:
            data = {
                'type': e.type,
                'status': e.status,
                'excerpt': e.excerpt,
                'e_id': e.entity_id
            }
            if e.known:
                data['name'] = e.name
            res.append(data)
        return res

    def add_evaluated_entity(self, evaluated_entity: EvaluatedEntity):
        self._content.add(evaluated_entity)

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

    async def populate_room_content_for_look(self, entity: Entity):
        from core.src.world.builder import world_repository
        await world_repository.populate_room_content_for_look(entity, self)
        return self
