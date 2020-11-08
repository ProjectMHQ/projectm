import inspect
import typing

from core.src.auth.logging_factory import LOGGER
from core.src.world.components.attributes import AttributesComponent
from core.src.world.components.base.abstract import ComponentType
from core.src.world.components.base.structcomponent import StructComponent
from core.src.world.components.inventory import InventoryComponent
from core.src.world.components.position import PositionComponent
from core.src.world.domain.entity import Entity


def get_base_room_for_entity(entity: Entity):
    return PositionComponent().set_list_coordinates([19, 1, 0])  # TODO FIXME


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


def get_entity_id_from_raw_data_input(text: str, data: typing.List, index: int = 0) -> typing.Optional[typing.Dict]:
    if not data:
        return None
    i = 0
    for entry in data:
        for x in entry['data']:
            print('Looking for %s at index %s, Examining %s (%s)' % (text, index, x, entry))
            if x['keyword'].startswith(text):
                if i == index:
                    return entry
                i += 1
    return None


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
        target: (PositionComponent, InventoryComponent)
):
    if isinstance(target, InventoryComponent):
        target.content.append(entity.entity_id)
        target.owned_by().set_for_update(target)
        entity.set_for_update(PositionComponent.parent_of.set(target.owned_by()).coords.set(''))
    elif isinstance(target, PositionComponent):
        entity.set_for_update(target)
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
                c_entity.set_component(PositionComponent().parent_of.set(container.owned_by()))
                return [c_entity]
        return []
    else:
        res = []
        assert keyword[-1] == '*'
        keyword = keyword.replace('*', '')
        for c_entity in container.populated:
            if c_entity.get_component(AttributesComponent).keyword.startswith(keyword):
                c_entity.set_component(PositionComponent().parent_of.set(container.owned_by()))
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
    components = [PosComponent, AttributesComponent, InventoryComponent]
    include_self and components.append(InventoryComponent)
    await load_components(entity, *components)
    from core.src.world.utils.world_utils import get_current_room
    room = await get_current_room(entity, populate=False)
    if not room.has_entities:
        return
    entities = [Entity(entity_id) for entity_id in room.entity_ids if entity_id != entity.entity_id]
    search_data = []
    if include_self:
        self_inventory = entity.get_component(InventoryComponent)
        entities = [Entity(e) for e in self_inventory.content] + entities
    entities and await batch_load_components(components, entities=entities)

    # filtering - todo: investigate how to improve it using indexes
    def _make_filters(_f_by):
        if not _f_by:
            return [], []
        from core.src.world.components.base.structcomponent import StructComponent
        _sb = []
        if issubclass(_f_by, StructComponent):
            _sb.append(_f_by)
        elif isinstance(_f_by, (tuple, list)):
            for _f in _f_by:
                if issubclass(_f, StructComponent):
                    _sb.append(_f)
                raise ValueError
        else:
            raise ValueError
        return _sb

    filters = _make_filters(filter_by)
    filtered = []
    for ent in entities:
        for component in components:
            if filters:
                for components in filters:
                    if ent.get_component(component) is None:
                        filtered.append(ent)
            if ent in filtered:
                continue
        # end filtering
    for ent in entities:
        if ent in filtered:
            continue
        search_data.append(
            {
                'entity_id': ent.entity_id,
                'data': [
                    {'keyword': ent.get_component(AttributesComponent).keyword.value}
                ],
                'entity': ent
            },
        )
    if include_self:
        self_attributes = entity.get_component(AttributesComponent)
        search_data.extend(
            [
                {
                    'entity_id': entity.entity_id,
                    'data': [
                        {'keyword': self_attributes.name.value},
                        {'keyword': self_attributes.keyword.value}
                    ],
                    'entity': entity
                }
            ]
        )
    if not search_data:
        return
    index, target = get_index_from_text(keyword)
    found = get_entity_id_from_raw_data_input(target, search_data, index=index)
    return found and found['entity']


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
    self_pos = self_entity.get_component(PositionComponent)
    await batch_load_components(PositionComponent, entities=entities)

    for e in entities:
        position = e.get_component(PositionComponent)
        if position.coords and position.coords != self_pos.coords:
            return False
        elif position.parent_of and position.parent_of != self_entity.entity_id:
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

    await batch_load_components(PositionComponent, (SystemComponent, 'connection'), entities=entities)
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
                entity.get_component(PositionComponent)
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
