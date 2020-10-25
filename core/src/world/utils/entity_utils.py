import inspect
import itertools
import typing

from core.src.auth.logging_factory import LOGGER
from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.base import ComponentType
from core.src.world.components.base.listcomponent import ListComponent
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
    return [data[x] for x in container.content]


def move_entity_from_container(
        entity: Entity,
        target: (PosComponent, InventoryComponent),
        current_position=None,
        parent: Entity = None
):
    if entity.get_component(PosComponent):
        current_position = current_position or entity.get_component(PosComponent)
        entity.set_for_update(PosComponent().add_previous_position(current_position))

    elif entity.get_component(ParentOfComponent):
        assert entity.get_component(ParentOfComponent).parent_id == parent.entity_id
        parent.set_for_update(InventoryComponent().content.remove(entity.entity_id))

    else:
        raise ValueError('Cannot recognize target original position data')

    if isinstance(target, InventoryComponent):
        target.content.append(entity.entity_id)
        target.owned_by().set_for_update(target)
        entity.set_for_update(ParentOfComponent(entity=target.owned_by(), location=target))
    elif isinstance(target, PosComponent):
        entity \
            .set_for_update(target) \
            .set_for_update(ParentOfComponent())
    else:
        raise ValueError('Target must be type PosComponent or ContainerComponent, is: %s' % target)
    return entity


async def search_entities_in_container_by_keyword(container: InventoryComponent, keyword: str) -> typing.List:
    """
    Search for entities in the provided container, using the keyword param.
    Accept a wildcard as the final character of the keyword argument, to search for multiple entities.
    """
    container_entities = await populate_container(container, AttributesComponent)
    if '*' not in keyword:
        for i, v in enumerate(container_entities):
            attr_comp_value = v[AttributesComponent.component_enum]
            if attr_comp_value['keyword'].startswith(keyword):
                entity = Entity(entity_id=container.content[i])\
                    .set_component(AttributesComponent(attr_comp_value))\
                    .set_component(
                    ParentOfComponent(entity=container.owned_by(), location=InventoryComponent)
                )
                return [entity]
        return []
    else:
        res = []
        assert keyword[-1] == '*'
        keyword = keyword.replace('*', '')
        for i, v in enumerate(container.populated):
            attr_comp_value = v[AttributesComponent.component_enum]
            if attr_comp_value['keyword'].startswith(keyword):
                entity = Entity(entity_id=container.content[i])\
                    .set_component(AttributesComponent(attr_comp_value))\
                    .set_component(
                    ParentOfComponent(entity=container.owned_by(), location=InventoryComponent)
                )
                res.append(entity)
        return res


async def search_entity_in_sight_by_keyword(
        entity, keyword, filter_by=None, include_self=True
) -> typing.Optional[Entity]:
    """
    Search entities in sight. By default can search itself (include_self=True)
    and it's containers (Inventory, Equipment): literally anything "in sight".

    entity: the searching Entity (type: Entity)
    keyword: the search params (doesn't accept wildcards)
    include_self: boolean param to include the searcher itself and its containers.

    Returns a single Entity or a None value.
    """
    if '*' in keyword:
        return
    from core.src.world.builder import world_repository
    if include_self:
        await load_components(entity, PosComponent, AttributesComponent, InventoryComponent)
    else:
        await load_components(entity, PosComponent, AttributesComponent)
    room = await get_current_room(entity)
    if not room.has_entities:
        return
    all_but_me = [eid for eid in room.entity_ids if eid != entity.entity_id]
    self_inventory = None
    if include_self:
        self_inventory = entity.get_component(InventoryComponent)
        all_but_me = self_inventory.content + all_but_me

    # filtering - investigate how to improve it
    components = [PosComponent, AttributesComponent, ParentOfComponent]

    def _make_filters(_f_by):
        if not _f_by:
            return [], []
        from core.src.world.components.base.structcomponent import StructComponent
        _fb = []
        _sb = []
        if issubclass(_f_by, StructComponent):
            _sb.append(_f_by)
        elif isinstance(_f_by, (tuple, list)):
            for _f in _f_by:
                if issubclass(_f, StructComponent):
                    _sb.append(_f)
                else:
                    _fb.append(_f)
        else:
            _fb.append(_f_by)
        return _fb, _sb

    filter_by, struct_filters = _make_filters(filter_by)
    _target_data = await world_repository.get_components_values_by_entities_ids(all_but_me, components)
    filtered = []
    target_data = {}
    for e_id, comp in _target_data.items():
        if not filter_by:
            target_data.update(_target_data)
        for c in filter_by:
            if _target_data.get(e_id, None) is None:
                target_data[e_id] = {}
            assert inspect.isclass(c)
            if comp[c.component_enum] is None:
                filtered.append(e_id)
        if e_id in filtered:
            continue
        if not target_data.get(e_id):
            target_data[e_id] = {}
        target_data[e_id].update({c: v for c, v in comp.items()})
    if struct_filters:
        struct_data = await world_repository.read_struct_components_for_entities(all_but_me, *struct_filters)
        for e_id, comp in struct_data.items():
            for c in struct_filters:
                if struct_data.get(e_id, None) is None:
                    target_data[e_id] = {}
                assert inspect.isclass(c)
                if comp[c.component_enum] is None:
                    filtered.append(e_id)
            if e_id in filtered:
                continue
            if not target_data.get(e_id):
                target_data[e_id] = {}
            target_data[e_id].update({c: v for c, v in comp.items()})
    # end filtering

    search_data = []
    attrs = entity.get_component(AttributesComponent)
    include_self and search_data.extend(
        [
            {
                'entity_id': entity.entity_id, 'data': [
                    {'keyword': attrs.name},
                    {'keyword': attrs.keyword}
                ]
            }
        ]
    )
    for entity_id in all_but_me:
        if entity_id in filtered:
            continue
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

    entity = Entity(found_entity_id).set_component(target_attributes)
    if self_inventory and found_entity_id in self_inventory.content:
        entity.set_component(
            ParentOfComponent(target_data[found_entity_id][ParentOfComponent.component_enum])
        )
    else:
        entity.set_component(PosComponent(target_data[found_entity_id][PosComponent.component_enum]))
    # Mount filtered components
    for f in filter_by:
        entity.set_component(f(target_data[found_entity_id][f.component_enum]))
    for f in struct_filters:
        assert isinstance(target_data[found_entity_id][f.component_enum], f)
        entity.set_component(target_data[found_entity_id][f.component_enum])
    # End
    return entity


async def search_entities_in_room_by_keyword(
    room: Room,
    keyword: str,
    filter_by: (ComponentType, typing.Tuple[ComponentType]) = None
) -> typing.List[Entity]:
    if not room.has_entities:
        return []
    if not room.content:
        await room.populate_content()  # Use the filter here
    if isinstance(filter_by, ComponentType):
        filter_by = (filter_by, )
        ent_filter = (type(x) for x in filter_by)
        await batch_load_components(*ent_filter, entities=room.entities)
    multiple_items = False
    if '*' in keyword:
        assert '*' not in keyword[1:]
        multiple_items = True
        keyword = keyword.replace('*', '')
    response = []
    for e in room.entities:
        if filter_by:
            filtered = False
            for c in filter_by:
                if e.get_component(type(c)).value != c.value:
                    filtered = True
            if filtered:
                continue
        if multiple_items and e.get_component(AttributesComponent).keyword.startswith(keyword):
            response.append(e.set_component(room.position))
        elif not multiple_items and e.get_component(AttributesComponent).keyword.startswith(keyword):
            return [e.set_component(room.position)]
    return response


async def ensure_same_position(self_entity: Entity, *entities: Entity) -> bool:
    """
    Ensures two or more entities are in the same position.
    Return a boolean.
    """
    assert self_entity.itsme
    pos0_value = self_entity.get_component(PosComponent).value
    assert pos0_value
    from core.src.world.builder import world_repository
    target_data = (
        await world_repository.get_components_values_by_entities_ids(
            list((e.entity_id for e in entities)),
            [PosComponent, ConnectionComponent, ParentOfComponent]
        )
    )
    for e in entities:
        if e.get_component(PosComponent):
            assert not e.get_component(ParentOfComponent)
            p_value = target_data[e.entity_id][PosComponent.component_enum]
            if p_value != pos0_value:
                return False
        elif e.get_component(ParentOfComponent):
            assert not e.get_component(PosComponent)
            p_value = target_data[e.entity_id][ParentOfComponent.component_enum]
            if p_value[0] != self_entity.entity_id:
                return False
        else:
            LOGGER.core.error('Cannot determinate if an item is in the same position as previous declared')
            return False
    return True


async def batch_load_components(*components, entities=()):
    """
    Load multiple components on multiple entities.
    Useful to load multiple components with a single DB interaction, and reduce DB load.
    """
    from core.src.world.builder import world_repository
    from core.src.world.components.base.structcomponent import StructComponent
    struct = []
    comps = []
    for c in components:
        if issubclass(c, StructComponent):
            struct.append(c)
        else:
            comps.append(c)
    struct_comps = struct and await world_repository.read_struct_components_for_entities((
        [e.entity_id for e in entities], *components
    )) or {}
    data = await world_repository.get_components_values_by_entities_ids([e.entity_id for e in entities], components)
    for entity in entities:
        for c in comps:
            comp = c(data[entity.entity_id][c.component_enum])
            comp.set_owner(entity)
            entity.set_component(comp)
    for entity in entities:
        for k, c in struct_comps.items():
            c.set_owner(entity)
            entity.set_component(c)
        return entity


async def load_components(entity, *components):
    """
    Load multiple components on multiple entities.
    Useful to load multiple components with a single DB interaction, and reduce DB load.
    """
    from core.src.world.builder import world_repository
    from core.src.world.components.base.structcomponent import StructComponent
    struct = []
    comps = []
    for c in components:
        if issubclass(c, StructComponent):
            struct.append(c)
        else:
            comps.append(c)
    struct_components = struct and \
                        (await world_repository.read_struct_components_for_entity(entity.entity_id, *struct)) or {}
    data = await world_repository.get_components_values_by_components_storage([entity.entity_id], comps)
    for legacy_c in comps:
        comp = legacy_c(data[legacy_c.component_enum][entity.entity_id])
        comp.set_owner(entity)
        entity.set_component(comp)
    for k, c in struct_components.items():
        c.set_owner(entity)
        entity.set_component(c)
    return entity


def update_entities(*entities, apply_bounds=True):
    """
    Batch updates all the entities passed.
    By default it uses Component Type specs to ensure critical bounds are set.
    """
    from core.src.world.builder import world_repository
    return world_repository.update_entities(*entities)
