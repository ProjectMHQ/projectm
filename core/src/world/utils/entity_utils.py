import typing

from core.src.world.builder import world_repository
from core.src.world.components import ComponentType
from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.character import CharacterComponent
from core.src.world.components.connection import ConnectionComponent
from core.src.world.components.inventory import InventoryComponent
from core.src.world.components.parent_of import ParentOfComponent
from core.src.world.components.pos import PosComponent
from core.src.world.domain.entity import Entity
from core.src.world.domain.room import Room
from core.src.world.utils.world_utils import get_current_room


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


async def populate_container(container: InventoryComponent, *components):
    from core.src.world.builder import world_repository
    data = await world_repository.get_components_values_by_entities(
        [Entity(x) for x in container.content], list(components)
    )
    container._raw_populated = data
    container._populated = [data[x] for x in container.content]
    return container


def remove_entity_from_container(entity: Entity, target: (PosComponent, InventoryComponent)):
    if isinstance(target, InventoryComponent):
        assert target.owned_by()
        target.add(entity.entity_id)
        entity \
            .set_for_update(PosComponent()) \
            .set_for_update(ParentOfComponent(entity=target.owned_by(), location=target))
    elif isinstance(target, PosComponent):
        entity \
            .set_for_update(target) \
            .set_for_update(ParentOfComponent())
    else:
        raise ValueError('Target must be type PosComponent or ContainerComponent')


async def search_entities_in_container_by_keyword(container: InventoryComponent, keyword: str) -> typing.List:
    """
    Search for entities in the provided container, using the keyword param.
    Accept a wildcard as the final character of the keyword argument, to search for multiple entities.
    """
    await populate_container(container, AttributesComponent)
    if '*' not in keyword:
        for i, v in enumerate(container.populated):
            attr_comp_value = v[AttributesComponent.component_enum]
            if attr_comp_value['keyword'].startswith(keyword):
                return [Entity(entity_id=container.content[i]).set_component(AttributesComponent(attr_comp_value))]
        return []
    else:
        res = []
        assert keyword[-1] == '*'
        keyword = keyword.replace('*', '')
        for i, v in enumerate(container.populated):
            attr_comp_value = v[AttributesComponent.component_enum]
            if attr_comp_value['keyword'].startswith(keyword):
                res.append(Entity(entity_id=container.content[i]).set_component(AttributesComponent(attr_comp_value)))
        return res


async def search_entity_in_sight_by_keyword(entity, keyword, include_self=True) -> typing.Optional[Entity]:
    """
    Search entities in sight. By default can search itself (include_self=True)
    and it's containers (Inventory, Equipment): literally anything "in sight".

    entity: the searching Entity (type: Entity)
    keyword: the search params (doesn't accept wildcards)
    include_self: boolean param to include the searcher itself and its containers.

    Returns a single Entity or a None value.
    """
    from core.src.world.builder import world_repository
    await load_components(entity, PosComponent, AttributesComponent)
    room = await get_current_room(entity)
    if not room.has_entities:
        return
    all_but_me = [eid for eid in room.entity_ids if eid != entity.entity_id]
    target_data = (
        await world_repository.get_components_values_by_entities_ids(all_but_me, [PosComponent, AttributesComponent])
    )
    search_data = []
    attrs = entity.get_component(AttributesComponent)
    include_self and search_data.extend(
        [
            {'entity_id': entity.entity_id, 'data': [
                {'keyword': attrs.name},
                {'keyword': attrs.keyword}
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
    return Entity(found_entity_id).set_component(entity.get_component(PosComponent)).set_component(target_attributes)


async def search_entities_in_room_by_keyword(
    room: Room,
    keyword: str,
    filter_by: (ComponentType, typing.Tuple[ComponentType]) = None
) -> typing.List[Entity]:
    """
    Search entities in the provided room by keyword (type: str).
    Can return multiple items using the wildcard '*' on the keyword param.
    filter_by keyword argument accepts a single Component or tuples of Components.
    """
    pass


async def ensure_same_position(itsme_entity: Entity, *entities: Entity) -> bool:
    """
    Ensures two or more entities are in the same position.
    Return a boolean.
    """
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
            comp = c(data[entity.entity_id][c.component_enum])
            comp.set_owner(entity)
            entity.set_component(comp)


async def load_components(entity, *components):
    """
    Load multiple components on multiple entities.
    Useful to load multiple components with a single DB interaction, and reduce DB load.
    """
    from core.src.world.builder import world_repository
    data = await world_repository.get_components_values_by_entities_ids([entity.entity_id], components)
    for c in components:
        comp = c(data[entity.entity_id][c.component_enum])
        comp.set_owner(entity)
        entity.set_component(comp)
    return entity


def update_entities(*entities, apply_bounds=True):
    """
    Batch updates all the entities passed.
    By default it uses Component Type specs to ensure critical bounds are set.
    """
    return world_repository.update_entities(entities)
