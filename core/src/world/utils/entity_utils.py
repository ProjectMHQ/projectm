import typing

from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.character import CharacterComponent
from core.src.world.components.connection import ConnectionComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.entity import Entity


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


def get_entity_id_from_raw_data_input(text: str, data: typing.List, index: int = 0) -> typing.Optional[typing.Tuple]:
    if not data:
        return
    i = 0
    for entry in data:
        for x in entry['data']:
            print('Looking for %s at index %s, Examining %s' % (text, index, x))
            if x['keyword'].startswith(text):
                if i == index:
                    return entry['entity_id'], x
                i += 1


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


async def search_entity_by_keyword(entity, keyword, include_self=True) -> typing.Optional[Entity]:
    from core.src.world.builder import world_repository, map_repository
    data = await world_repository.get_components_values_by_entities(
        [entity],
        [PosComponent, AttributesComponent]
    )
    pos = PosComponent(data[entity.entity_id][PosComponent.component_enum])
    attrs_value = data[entity.entity_id][AttributesComponent.component_enum]
    room = await map_repository.get_room(pos)
    entity.set_component(AttributesComponent(attrs_value)).set_component(pos).set_room(room)
    if not room.has_entities:
        return
    all_but_me = [eid for eid in room.entity_ids if eid != entity.entity_id]
    target_data = (
        await world_repository.get_components_values_by_entities_ids(all_but_me, [PosComponent, AttributesComponent])
    )
    search_data = []
    include_self and search_data.extend(
        [
            {'entity_id': entity.entity_id, 'data': [
                {'keyword': attrs_value['name']},
                {'keyword': attrs_value['keyword']}
            ]},
        ]
    )
    for entity_id in all_but_me:
        search_data.append(
            {'entity_id': entity_id, 'data': [
                {'keyword': target_data[entity_id][AttributesComponent.component_enum]['keyword']}
            ]},
        )
    if not search_data:
        return
    index, target = get_index_from_text(keyword)
    found_entity = get_entity_id_from_raw_data_input(target, search_data, index=index)
    if found_entity and found_entity[0]:
        found_entity_id, _ = found_entity
    else:
        return
    if entity.entity_id == found_entity_id:
        target_attributes = entity.get_component(AttributesComponent)
    else:
        target_attributes = AttributesComponent(target_data[found_entity_id][AttributesComponent.component_enum])
    return Entity(found_entity_id).set_component(pos).set_component(target_attributes)


async def ensure_same_position(itsme_entity: Entity, *entities: Entity):
    assert itsme_entity.itsme
    pos0_value = itsme_entity.get_component(PosComponent).value
    assert pos0_value
    from core.src.world.builder import world_repository
    target_data = (
        await world_repository.get_components_values_by_entities_ids(
            list((e.entity_id for e in entities)),
            [PosComponent, ConnectionComponent, CharacterComponent]
        )
    )
    for e in entities:
        p_value = target_data[e.entity_id][PosComponent.component_enum]
        if p_value != pos0_value:
            return False
        e.set_component(PosComponent(p_value))
        e.set_component(CharacterComponent(
            target_data[e.entity_id][CharacterComponent.component_enum]
        ))
    return True


async def batch_load_components(*components, entities=()):
    """
    Load multiple components on multiple entities.
    Useful to load multiple components with a single DB interaction, and reduce DB load.
    """
    from core.src.world.builder import world_repository
    data = await world_repository.get_components_values_by_entities_ids([e.entity_id for e in entities], components)
    for entity in entities:
        for c in components:
            entity.set_component(c(data[entity.entity_id][c.component_enum]))


async def load_components(entity, *components):
    """
    Load multiple components on multiple entities.
    Useful to load multiple components with a single DB interaction, and reduce DB load.
    """
    from core.src.world.builder import world_repository
    data = await world_repository.get_components_values_by_entities_ids([entity.entity_id], components)
    for c in components:
        entity.set_component(c(data[entity.entity_id][c.component_enum]))
