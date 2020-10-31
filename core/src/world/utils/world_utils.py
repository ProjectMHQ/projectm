import typing

from core.src.auth.logging_factory import LOGGER
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
        entity.set_component(PosComponent(pos[entity.entity_id][PosComponent.enum]))
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


async def clean_rooms_from_stales_instances(instance_type='character'):
    from core.src.world.components.system import SystemComponent
    from core.src.world.builder import world_repository
    from core.src.world.utils.entity_utils import batch_load_components
    from core.src.world.actions.system.disconnect import disconnect_entity
    from core.src.world.builder import map_repository
    entity_ids_with_connection_component_active = await world_repository.get_entity_ids_with_components_having_value(
        (SystemComponent, 'instance_of', instance_type)
    )
    if not entity_ids_with_connection_component_active:
        return []
    entities = [Entity(eid) for eid in entity_ids_with_connection_component_active]
    await batch_load_components(PosComponent, SystemComponent, entities=entities)
    entities_without_connection_component_and_position = [
        e for e in entities if not e.get_component(SystemComponent).connection.value
        and e.get_component(PosComponent).value
    ]
    rooms = await map_repository.get_rooms(
        *(e.get_component(PosComponent) for e in entities_without_connection_component_and_position)
    )
    stales = []
    for i, room in enumerate(rooms):
        if entities_without_connection_component_and_position[i].entity_id in room.entity_ids:
            stales.append(entities_without_connection_component_and_position[i])
    LOGGER.core.error('Error, found stales entities: %s' % str([x.entity_id for x in stales]))
    for entity in stales:
        await disconnect_entity(entity, msg=False)
