import typing

from core.src.world.components.pos import PosComponent
from core.src.world.domain.entity import Entity
from core.src.world.utils.world_types import DirectionEnum, TerrainEnum


def direction_to_coords_delta(direction: object) -> typing.Tuple:
    return {
        DirectionEnum.NORTH: (0, 1, 0),
        DirectionEnum.SOUTH: (0, -1, 0),
        DirectionEnum.EAST: (1, 0, 0),
        DirectionEnum.WEST: (-1, 0, 0),
        DirectionEnum.UP: (0, 0, 1),
        DirectionEnum.DOWN: (0, 0, -1),
    }[direction]


def apply_delta_to_position(room_position: PosComponent, delta: typing.Tuple[int, int, int]):
    return PosComponent([
        room_position.x + delta[0],
        room_position.y + delta[1],
        room_position.z + delta[2]
        ]
    )


def get_direction(direction):
    assert direction not in ('u', 'd'), 'not supported yet'
    try:
        return DirectionEnum(direction)
    except:
        return None


def is_terrain_walkable(terrain_type: TerrainEnum):
    return {
        TerrainEnum.NULL: False,
        TerrainEnum.WALL_OF_BRICKS: False,
        TerrainEnum.PATH: True,
        TerrainEnum.GRASS: True
    }[terrain_type]


async def get_current_room(entity: Entity, populate=True):
    from core.src.world.builder import world_repository
    from core.src.world.builder import map_repository
    if not entity.get_component(PosComponent):
        pos = await world_repository.get_components_values_by_entities_ids(
            [entity.entity_id],
            [PosComponent]
        )
        entity.set_component(PosComponent(pos[entity.entity_id][PosComponent.component_enum]))
    room = await map_repository.get_room(entity.get_component(PosComponent), populate=populate)
    populate and await room.populate_content()
    entity.set_room(room)
    return room


async def get_room_at_direction(entity: Entity, direction_enum, populate=True):
    from core.src.world.builder import map_repository, world_repository
    delta = direction_to_coords_delta(direction_enum)
    if not delta:
        return
    pos = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
    entity.set_component(pos)
    look_cords = apply_delta_to_position(pos, delta)
    room = await map_repository.get_room(look_cords, populate=populate)
    populate and await room.populate_content()
    return room
