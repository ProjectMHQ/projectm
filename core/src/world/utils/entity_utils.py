import itertools
import typing

from core.src.world.actions.movement._utils_ import direction_to_coords_delta, apply_delta_to_position
from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.entity import Entity
from core.src.world.utils.world_types import SearchResponse


def get_base_room_for_entity(entity: Entity):
    return PosComponent([19, 1, 0])  # TODO FIXME


def get_index_from_text(text: str) -> typing.Tuple[int, str]:
    if '.' in text:
        _split = text.split('.')
        if len(_split) > 2:
            raise ValueError
        index = int(_split[0]) - 1
        text = _split[1]
    else:
        index = 0
    return index, text


def get_entity_id_from_raw_data_input(
        text: str, totals: int, data: typing.Iterable, index: int = 0
) -> typing.Optional[typing.Tuple]:
    if not data:
        return
    i = 0
    entity_id = None
    keyword = None
    for x in range(0, totals):
        for entry in data:
            if entry['data'][x]['keyword'].startswith(text):
                if i == index:
                    entity_id = entry['entity_id']
                    keyword = entry['data'][x]['keyword']
                    break
                i += 1
    return entity_id, keyword


def get_entity_data_from_raw_data_input(
        text: str, totals: int, data: typing.Iterable, index: int = 0
) -> typing.Optional[typing.Dict]:
    if not data:
        return
    i = 0
    for x in range(0, totals):
        for entry in data:
            if entry['data'][x]['keyword'].startswith(text):
                if i == index:
                    return entry
                i += 1


async def search_entity_by_keyword(entity, keyword, include_self=True) -> SearchResponse:
    from core.src.world.builder import world_repository, map_repository
    data = await world_repository.get_components_values_by_entities(
        [entity],
        [PosComponent, AttributesComponent]
    )
    pos = PosComponent(data[entity.entity_id][PosComponent.component_enum])
    attrs_value = data[entity.entity_id][AttributesComponent.component_enum]
    room = await map_repository.get_room(PosComponent([pos.x, pos.y, pos.z]))
    if not room.has_entities:
        return
    await room.populate_room_content_for_look(entity)
    totals, raw_room_content = await world_repository.get_raw_content_for_room_interaction(entity.entity_id, room)
    if include_self:
        personal_data = [
            {
                'entity_id': entity.entity_id, 'data': [attrs_value, *('' for _ in range(1, totals))]
            },
            {
                'entity_id': entity.entity_id, 'data': [{'keyword': attrs_value['name']}]
            },
        ]

        raw_room_content = itertools.chain(raw_room_content, personal_data)
    index, target = get_index_from_text(keyword)
    found_entity = get_entity_id_from_raw_data_input(target, totals, raw_room_content, index=index)
    if found_entity and found_entity[0]:
        found_entity_id, keyword = found_entity
    else:
        return
    return SearchResponse(
        search_origin_attributes=AttributesComponent(attrs_value),
        room=room,
        entity_id=found_entity_id,
        keyword=keyword
    )


async def get_current_room(entity: Entity, populate=True):
    from core.src.world.builder import world_repository
    from core.src.world.builder import map_repository
    pos = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
    room = await map_repository.get_room(pos, populate=populate)
    return room


async def get_room_at_direction(entity: Entity, direction_enum, populate=True):
    from core.src.world.builder import map_repository, world_repository
    delta = direction_to_coords_delta(direction_enum)
    if not delta:
        return
    pos = await world_repository.get_component_value_by_entity_id(entity.entity_id, PosComponent)
    look_cords = apply_delta_to_position(pos, delta)
    room = await map_repository.get_room(look_cords, populate=populate)
    return room
