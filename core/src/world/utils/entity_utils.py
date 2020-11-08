import inspect
import typing

from core.src.auth.logging_factory import LOGGER
from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.base import ComponentType
from core.src.world.components.base.structcomponent import StructComponent
from core.src.world.components.inventory import InventoryComponent
from core.src.world.components.parent_of import ParentOfComponent
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
            print('Looking for %s at index %s, Examining %s (%s)' % (text, index, x, entry))
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
    container._raw_populated = [Entity(x) for x in container.content]
    container._raw_populated and await batch_load_components(*components, entities=container._raw_populated)
    return container


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
    await populate_container(container, AttributesComponent)
    if '*' not in keyword:
        for c_entity in container.populated:
            if c_entity.get_component(AttributesComponent).keyword.startswith(keyword):
                c_entity.set_component(
                    ParentOfComponent(entity=container.owned_by(), location=InventoryComponent)
                )
                return [c_entity]
        return []
    else:
        res = []
        assert keyword[-1] == '*'
        keyword = keyword.replace('*', '')
        for c_entity in container.populated:
            if c_entity.get_component(AttributesComponent).keyword.startswith(keyword):
                c_entity.set_component(
                    ParentOfComponent(entity=container.owned_by(), location=InventoryComponent)
                )
                res.append(c_entity)
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
    from core.src.world.utils.world_utils import get_current_room
    room = await get_current_room(entity)
    if not room.has_entities:
        return
    all_but_me = [eid for eid in room.entity_ids if eid != entity.entity_id]
    search_data = []
    target_data = {}
    self_inventory = None
    if include_self:
        self_inventory = entity.get_component(InventoryComponent)
        all_but_me = self_inventory.content + all_but_me

    # filtering - investigate how to improve it
    components = [PosComponent, ParentOfComponent]
    struct_components = [AttributesComponent]

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

    if all_but_me:
        filtered = []
        _target_data = await world_repository.get_components_values_by_entities_ids(all_but_me, components)
        for e_id, comp in _target_data.items():
            if not filter_by:
                target_data.update(_target_data)
            for c in filter_by:
                if _target_data.get(e_id, None) is None:
                    target_data[e_id] = {}
                assert inspect.isclass(c)
                if comp[c.enum] is None:
                    filtered.append(e_id)
            if e_id in filtered:
                continue
            if not target_data.get(e_id):
                target_data[e_id] = {}
            target_data[e_id].update({c: v for c, v in comp.items()})
        struct_components = list(struct_components) + list(struct_filters)
        struct_data = await world_repository.read_struct_components_for_entities(all_but_me, *struct_components)
        for e_id, comp in struct_data.items():
            if struct_filters:
                for c in struct_filters:
                    assert inspect.isclass(c)
                    if comp[c.enum] is None:
                        filtered.append(e_id)
            if e_id in filtered:
                continue
            if not target_data.get(e_id):
                target_data[e_id] = {}
            target_data[e_id].update({c: v for c, v in comp.items()})
        # end filtering
        for entity_id in all_but_me:
            if entity_id in filtered:
                continue
            search_data.append(
                {'entity_id': entity_id, 'data': [
                    {'keyword': target_data[entity_id][AttributesComponent.enum].keyword.value}
                ]},
            )
    attrs = entity.get_component(AttributesComponent)
    include_self and search_data.extend(
        [
            {
                'entity_id': entity.entity_id, 'data': [
                    {'keyword': attrs.name.value},
                    {'keyword': attrs.keyword.value}
                ]
            }
        ]
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
        target_attributes = target_data[found_entity_id][AttributesComponent.enum]

    ent = Entity(found_entity_id).set_component(target_attributes)
    if self_inventory and found_entity_id in self_inventory.content:
        ent.set_component(
            ParentOfComponent(target_data[found_entity_id][ParentOfComponent.enum])
        )
    elif entity.entity_id != found_entity_id:
        ent.set_component(PosComponent(target_data[found_entity_id][PosComponent.enum]))
    # Mount filtered components
    for f in filter_by:
        ent.set_component(f(target_data[found_entity_id][f.enum]))
    for f in struct_filters:
        assert isinstance(target_data[found_entity_id][f.enum], f)
        ent.set_component(target_data[found_entity_id][f.enum])
    # End
    return ent


async def search_entities_in_room_by_keyword(
    room,
    keyword: str,
    filter_by: (StructComponent, typing.Tuple[ComponentType]) = None
) -> typing.List[Entity]:
    if not room.has_entities:
        return []
    if not room.content:
        await room.populate_content()  # Use the filter here
    if inspect.isclass(filter_by) and issubclass(filter_by, StructComponent):
        filter_by = (filter_by, )
    elif isinstance(filter_by, tuple) and inspect.isclass(filter_by[0]) and issubclass(filter_by[0], StructComponent):
        pass
    else:
        raise ValueError
    components = [AttributesComponent]
    if filter_by[0] not in components:
        if len(filter_by) > 1:
            components.append((filter_by[0], filter_by[1]))
        else:
            components.append(filter_by[0])
    await batch_load_components(*components, entities=room.entities)
    multiple_items = False
    if '*' in keyword:
        assert '*' not in keyword[1:]
        multiple_items = True
        keyword = keyword.replace('*', '')
    response = []
    for e in room.entities:
        if filter_by:
            filtered = False
            if not e.get_component(filter_by[0]):
                filtered = True
            else:
                if len(filter_by) == 3:
                    if e.get_component(filter_by[0]).get_value(filter_by[1]) != filter_by[2]:
                        filtered = True
                elif len(filter_by) == 2 and not e.get_component(filter_by[0]).get_value(filter_by[1]):
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
            [PosComponent, ParentOfComponent]
        )
    )
    for e in entities:
        if e.get_component(PosComponent):
            assert not e.get_component(ParentOfComponent)
            p_value = target_data[e.entity_id][PosComponent.enum]
            if p_value != pos0_value:
                return False
        elif e.get_component(ParentOfComponent):
            assert not e.get_component(PosComponent)
            p_value = target_data[e.entity_id][ParentOfComponent.enum]
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
        if (isinstance(c, tuple) and (inspect.isclass(c[0]) and issubclass(c[0], StructComponent))) or \
                (inspect.isclass(c) and issubclass(c, StructComponent)):
            struct.append(c)
        else:
            comps.append(c)
    struct_comps = struct and await world_repository.read_struct_components_for_entities(
        [e.entity_id for e in entities], *struct
    ) or {}
    data = await world_repository.get_components_values_by_entities_ids([e.entity_id for e in entities], comps)
    for entity in entities:
        for c in comps:
            assert not isinstance(c, tuple)
            comp = c(data[entity.entity_id][c.enum])
            comp.set_owner(entity)
            entity.set_component(comp)
    for entity in entities:
        entity_comps = struct_comps.get(entity.entity_id, {})
        for ck, cv in entity_comps.items():
            cv.set_owner(entity)
            entity.set_component(cv)
    return entities


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
        if (isinstance(c, tuple) and (inspect.isclass(c[0]) and issubclass(c[0], StructComponent))) or \
                (inspect.isclass(c) and issubclass(c, StructComponent)):
            struct.append(c)
        else:
            comps.append(c)
    struct_components = struct and \
                        (await world_repository.read_struct_components_for_entity(entity.entity_id, *struct)) or {}
    data = await world_repository.get_components_values_by_components_storage([entity.entity_id], comps)
    for legacy_c in comps:
        comp = legacy_c(data[legacy_c.enum][entity.entity_id])
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


async def check_entities_connection_status() -> typing.List[typing.Dict]:
    """
    Check the match between the transport repository and the ECS status.
    If Entities with Connection component valued are found, but there is no match in the repository,
    the channel is removed from the ECS and the entity is removed from the room.

    Return details on the still active entities.
    """
    from core.src.world.builder import world_repository
    from core.src.world.components.system import SystemComponent
    from core.src.world.builder import channels_repository
    from core.src.world.builder import map_repository, cmds_observer

    entity_ids_with_connection_component_active = await world_repository.get_entity_ids_with_valued_components(
        (SystemComponent, 'connection')
    )
    if not entity_ids_with_connection_component_active:
        return []
    entities = [Entity(eid) for eid in entity_ids_with_connection_component_active]

    await batch_load_components(PosComponent, (SystemComponent, 'connection'), entities=entities)
    components_values = []
    entities_by_id = {}
    for entity in entities:
        components_values.append(entity.get_component(SystemComponent).connection.value)
        entities_by_id[entity.entity_id] = entity
    to_update = []
    online = []
    if not components_values:
        return online
    channels = channels_repository.get_many(*components_values)
    for i, ch in enumerate(channels.values()):
        if not ch:
            entity = entities[i]
            to_update.append(entity)
            await map_repository.remove_entity_from_map(
                entity_ids_with_connection_component_active[i],
                entity.get_component(PosComponent)
            )
        else:
            cmds_observer.enable_channel(ch.id)
            online.append(
                {
                    'entity_id': entity_ids_with_connection_component_active[i],
                    'channel_id': ch.id
                }
            )
    await world_repository.update_entities(*to_update)
    return online
