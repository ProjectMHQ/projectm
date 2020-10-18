import typing

from core.src.world.components.pos import PosComponent
from core.src.world.domain import DomainObject
from core.src.world.utils.world_types import TerrainEnum, EvaluatedEntity
from core.src.world.utils.world_utils import is_terrain_walkable


class Room(DomainObject):
    item_type = "room"

    def __init__(
        self,
        position: PosComponent = None,
        terrain: TerrainEnum = TerrainEnum.NULL,
        entity_ids: typing.List[int] = list()
    ):
        self._position = position
        self._terrain = terrain
        self._entity_ids = entity_ids
        self._content: typing.Set[EvaluatedEntity] = set()
        self._pov_direction = None

    def set_pov_direction(self, value):
        self._pov_direction = value
        return self

    def pov_direction(self):
        return self._pov_direction

    @property
    def position(self) -> PosComponent:
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

    def serialize(self) -> typing.Dict:
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
        return {
            "position": [self._position.x, self._position.y, self._position.z],
            "content": res
        }

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

    async def populate_content(self, entity):
        from core.src.world.builder import world_repository
        await world_repository.populate_room_content_for_look(entity, self)
        return self

    async def refresh(self, populate=False):
        from core.src.world.builder import map_repository
        room = await map_repository.get_room(self.position, populate=populate)
        self._terrain = room.terrain
        # FIXME TODO
        return self
